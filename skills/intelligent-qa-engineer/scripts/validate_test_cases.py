#!/usr/bin/env python3
"""Validate test-case CSVs and, optionally, a traceability matrix.

Standard library only (Python 3.9+). Usage:

    python validate_test_cases.py test-cases.csv
    python validate_test_cases.py test-cases.csv --traceability traceability-matrix.csv
    python validate_test_cases.py test-cases.csv --json

Exit codes: 0 = valid (warnings allowed), 1 = validation errors
(or warnings with --strict), 2 = usage or file error.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

CASE_COLUMNS = [
    "test_case_id",
    "requirement_id",
    "title",
    "objective",
    "priority",
    "preconditions",
    "test_data",
    "steps",
    "expected_result",
    "test_type",
    "technique",
    "automation",
    "tags",
]
CASE_REQUIRED_VALUES = [
    "test_case_id",
    "requirement_id",
    "title",
    "objective",
    "priority",
    "steps",
    "expected_result",
    "test_type",
    "automation",
]
MATRIX_COLUMNS = [
    "requirement_id",
    "requirement_summary",
    "source",
    "priority",
    "risk_ids",
    "test_case_ids",
    "coverage_status",
    "notes",
]

PRIORITIES = {"Critical", "High", "Medium", "Low"}
TEST_TYPES = {
    "Functional", "API", "Integration", "Unit", "E2E", "Regression", "Smoke",
    "Security", "Performance", "Contract", "Usability", "Accessibility",
}
AUTOMATION = {"Automate", "Candidate", "Manual"}
TECHNIQUES = {
    "EP", "BVA", "Decision table", "State transition", "Pairwise",
    "Error guessing", "Risk-based", "Use case", "Exploratory",
}
COVERAGE_STATUSES = {"Covered", "Partial", "Not covered", "Untestable", "Blocked"}
STATUSES_WITHOUT_TESTS = {"Not covered", "Untestable", "Blocked"}

TEST_ID_RE = re.compile(r"^TC-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3,}$")
REQ_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]*$")
VAGUE_RESULTS = re.compile(
    r"^\s*(works( correctly| as expected)?|as expected|ok|success|it works|"
    r"funciona( correctamente)?|correcto|según lo esperado)\.?\s*$",
    re.IGNORECASE,
)

# High-confidence secret patterns -> error. Lower-confidence -> warning.
SECRET_PATTERNS = {
    "AWS access key id": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{22,}\b"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    "OpenAI/Anthropic-style API key": re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
}
SUSPICIOUS_PATTERNS = {
    "JWT-like token": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "inline password assignment": re.compile(r"(?i)\b(?:password|passwd|pwd)\s*[:=]\s*(?!\$\{|<|\*{3}|\{\{)[^\s;|,]{6,}"),
}


@dataclass
class Report:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: Dict[str, object] = field(default_factory=dict)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def split_multi(value: str) -> List[str]:
    """Split a ';' separated cell into trimmed, non-empty items."""
    return [part.strip() for part in (value or "").split(";") if part.strip()]


def scan_text_for_secrets(text: str, where: str, report: Report) -> None:
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            report.error(f"{where}: possible {label} found; use a placeholder or environment variable")
    for label, pattern in SUSPICIOUS_PATTERNS.items():
        if pattern.search(text):
            report.warn(f"{where}: {label} found; confirm it is a fake, non-sensitive value")


def read_csv(path: Path) -> tuple:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = [h.strip() for h in (reader.fieldnames or [])]
        rows = []
        for row in reader:
            clean = {}
            for key, value in row.items():
                if key is None:
                    clean["__extra__"] = value
                    continue
                clean[key.strip()] = (value or "").strip() if isinstance(value, str) else ""
            rows.append(clean)
    return header, rows


def check_header(header: Sequence[str], expected: Sequence[str], name: str, report: Report) -> bool:
    missing = [c for c in expected if c not in header]
    if missing:
        report.error(f"{name}: missing required column(s): {', '.join(missing)}")
    extra = [c for c in header if c not in expected]
    if extra:
        report.warn(f"{name}: unknown column(s) ignored: {', '.join(extra)}")
    dupes = [c for c, n in Counter(header).items() if n > 1]
    if dupes:
        report.error(f"{name}: duplicated column(s): {', '.join(dupes)}")
    return not missing and not dupes


def validate_cases(rows: List[dict], report: Report) -> Dict[str, dict]:
    cases: Dict[str, dict] = {}
    titles: Counter = Counter()
    if not rows:
        report.error("test cases: file has no data rows")
    for index, row in enumerate(rows, start=2):  # header is line 1
        where = f"test cases line {index}"
        if "__extra__" in row:
            report.error(f"{where}: more values than columns (unquoted comma?)")
        tc_id = row.get("test_case_id", "")
        if tc_id:
            where = f"{where} ({tc_id})"
        for column in CASE_REQUIRED_VALUES:
            if not row.get(column):
                report.error(f"{where}: '{column}' is empty")
        for column in ("preconditions", "test_data"):
            if not row.get(column):
                report.warn(f"{where}: '{column}' is empty (use 'None' if not applicable)")
        if tc_id and not TEST_ID_RE.match(tc_id):
            report.error(f"{where}: test_case_id must match TC-<AREA>-<NNN> (e.g. TC-CUS-001)")
        if tc_id in cases:
            report.error(f"{where}: duplicated test_case_id")
        for req in split_multi(row.get("requirement_id", "")):
            if not REQ_ID_RE.match(req):
                report.error(f"{where}: invalid requirement_id '{req}'")
        _check_enum(row, "priority", PRIORITIES, where, report, error=True)
        _check_enum(row, "test_type", TEST_TYPES, where, report, error=True)
        _check_enum(row, "automation", AUTOMATION, where, report, error=True)
        if row.get("technique"):
            for technique in split_multi(row["technique"]):
                if technique not in TECHNIQUES:
                    report.warn(f"{where}: unknown technique '{technique}'")
        else:
            report.warn(f"{where}: 'technique' is empty")
        expected = row.get("expected_result", "")
        if expected and VAGUE_RESULTS.match(expected):
            report.error(f"{where}: expected_result is not verifiable ('{expected}')")
        steps = row.get("steps", "")
        if steps and "|" not in steps and len(steps) < 15:
            report.warn(f"{where}: steps look too short to be reproducible")
        title = row.get("title", "").lower()
        if title:
            titles[title] += 1
        scan_text_for_secrets(" ".join(v for k, v in row.items() if k != "__extra__" and isinstance(v, str)), where, report)
        if tc_id and tc_id not in cases:
            cases[tc_id] = row
    for title, count in titles.items():
        if count > 1:
            report.warn(f"test cases: title used {count} times, possible duplicate cases: '{title}'")
    return cases


def _check_enum(row: dict, column: str, allowed: set, where: str, report: Report, error: bool) -> None:
    value = row.get(column, "")
    if value and value not in allowed:
        message = f"{where}: '{column}' value '{value}' not in {sorted(allowed)}"
        (report.error if error else report.warn)(message)


def validate_matrix(rows: List[dict], cases: Dict[str, dict], report: Report) -> Dict[str, dict]:
    matrix: Dict[str, dict] = {}
    if not rows:
        report.error("traceability: file has no data rows")
    for index, row in enumerate(rows, start=2):
        req = row.get("requirement_id", "")
        where = f"traceability line {index}" + (f" ({req})" if req else "")
        if "__extra__" in row:
            report.error(f"{where}: more values than columns (unquoted comma?)")
        if not req:
            report.error(f"{where}: 'requirement_id' is empty")
            continue
        if req in matrix:
            report.error(f"{where}: duplicated requirement_id")
        if not row.get("requirement_summary"):
            report.error(f"{where}: 'requirement_summary' is empty")
        status = row.get("coverage_status", "")
        if status not in COVERAGE_STATUSES:
            report.error(f"{where}: coverage_status '{status}' not in {sorted(COVERAGE_STATUSES)}")
        if row.get("priority") and row["priority"] not in PRIORITIES:
            report.error(f"{where}: priority '{row['priority']}' not in {sorted(PRIORITIES)}")
        tests = split_multi(row.get("test_case_ids", ""))
        for tc_id in tests:
            if tc_id not in cases:
                report.error(f"{where}: references unknown test case '{tc_id}'")
            elif req not in split_multi(cases[tc_id].get("requirement_id", "")):
                report.warn(f"{where}: {tc_id} is listed here but its requirement_id does not include {req}")
        if not tests and status in {"Covered", "Partial"}:
            report.error(f"{where}: status '{status}' but no test_case_ids")
        if tests and status in STATUSES_WITHOUT_TESTS - {"Blocked"}:
            report.warn(f"{where}: status '{status}' but test cases are linked")
        scan_text_for_secrets(" ".join(v for k, v in row.items() if k != "__extra__" and isinstance(v, str)), where, report)
        matrix[req] = row
    # Every requirement referenced by a test must exist in the matrix, and
    # every (test, requirement) link should be listed in the matrix.
    for tc_id, case in cases.items():
        for req in split_multi(case.get("requirement_id", "")):
            if req not in matrix:
                report.error(f"test {tc_id}: requirement '{req}' is not in the traceability matrix")
            elif tc_id not in split_multi(matrix[req].get("test_case_ids", "")):
                report.warn(f"test {tc_id}: not listed under requirement '{req}' in the traceability matrix")
    return matrix


def build_summary(cases: Dict[str, dict], matrix: Optional[Dict[str, dict]]) -> Dict[str, object]:
    summary: Dict[str, object] = {
        "test_cases": len(cases),
        "by_priority": dict(Counter(c.get("priority", "") for c in cases.values())),
        "by_type": dict(Counter(c.get("test_type", "") for c in cases.values())),
        "by_automation": dict(Counter(c.get("automation", "") for c in cases.values())),
    }
    if matrix is not None:
        with_tests = sum(1 for r in matrix.values() if split_multi(r.get("test_case_ids", "")))
        summary["requirements"] = len(matrix)
        summary["requirements_with_tests"] = with_tests
        summary["requirement_coverage"] = (
            f"{with_tests}/{len(matrix)} ({with_tests / len(matrix):.0%})" if matrix else "n/a"
        )
        summary["by_coverage_status"] = dict(Counter(r.get("coverage_status", "") for r in matrix.values()))
    return summary


def validate(cases_path: Path, matrix_path: Optional[Path] = None) -> Report:
    report = Report()
    header, rows = read_csv(cases_path)
    cases: Dict[str, dict] = {}
    if check_header(header, CASE_COLUMNS, "test cases", report):
        cases = validate_cases(rows, report)
    matrix = None
    if matrix_path is not None:
        m_header, m_rows = read_csv(matrix_path)
        if check_header(m_header, MATRIX_COLUMNS, "traceability", report):
            matrix = validate_matrix(m_rows, cases, report)
    report.summary = build_summary(cases, matrix)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate QA test-case CSVs and traceability matrices.")
    parser.add_argument("cases", type=Path, help="test cases CSV (see assets/templates/test-cases.csv)")
    parser.add_argument("--traceability", "-t", type=Path, help="traceability matrix CSV")
    parser.add_argument("--json", action="store_true", help="print a machine-readable JSON report")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = parser.parse_args(argv)

    for path in filter(None, [args.cases, args.traceability]):
        if not path.is_file():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2
    try:
        report = validate(args.cases, args.traceability)
    except (csv.Error, UnicodeDecodeError) as exc:
        print(f"error: could not parse CSV: {exc}", file=sys.stderr)
        return 2

    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    if args.json:
        print(json.dumps({
            "valid": not failed,
            "errors": report.errors,
            "warnings": report.warnings,
            "summary": report.summary,
        }, indent=2, ensure_ascii=False))
    else:
        for message in report.errors:
            print(f"ERROR   {message}")
        for message in report.warnings:
            print(f"WARNING {message}")
        print("Summary:")
        for key, value in report.summary.items():
            print(f"  {key}: {value}")
        print(f"Result: {'INVALID' if failed else 'VALID'} "
              f"({len(report.errors)} error(s), {len(report.warnings)} warning(s))")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
