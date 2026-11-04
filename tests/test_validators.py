"""Unit tests for skills/intelligent-qa-engineer/scripts/validate_test_cases.py."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import SKILL_DIR

SCRIPT = SKILL_DIR / "scripts" / "validate_test_cases.py"

GOOD_CASE = {
    "test_case_id": "TC-LOGIN-001",
    "requirement_id": "AC-1",
    "title": "Rejects wrong password",
    "objective": "Verify a wrong password is rejected",
    "priority": "High",
    "preconditions": "User u1 exists",
    "test_data": "password=<wrong-password>",
    "steps": "1. Open login | 2. Enter u1 and a wrong password | 3. Submit",
    "expected_result": "Message 'Invalid credentials'; user stays on login page",
    "test_type": "Functional",
    "technique": "EP",
    "automation": "Automate",
    "tags": "negative;auth",
}
GOOD_ROW = {
    "requirement_id": "AC-1",
    "requirement_summary": "Wrong passwords are rejected",
    "source": "Story AC-1",
    "priority": "High",
    "risk_ids": "",
    "test_case_ids": "TC-LOGIN-001",
    "coverage_status": "Covered",
    "notes": "",
}


def write_csv(path: Path, columns, rows) -> Path:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return path


@pytest.fixture
def files(tmp_path, validator):
    def _make(cases=None, rows=None):
        cases_path = write_csv(tmp_path / "cases.csv", validator.CASE_COLUMNS, cases or [GOOD_CASE])
        matrix_path = write_csv(tmp_path / "matrix.csv", validator.MATRIX_COLUMNS, rows or [GOOD_ROW]) \
            if rows is not False else None
        return cases_path, matrix_path
    return _make


def run(validator, files, **kwargs):
    cases, matrix = files(**kwargs)
    return validator.validate(cases, matrix)


def test_valid_files_have_no_findings(validator, files):
    report = run(validator, files)
    assert report.errors == [] and report.warnings == []
    assert report.summary["requirement_coverage"] == "1/1 (100%)"


def test_cases_without_matrix(validator, files):
    report = run(validator, files, rows=False)
    assert report.errors == []
    assert "requirements" not in report.summary


def test_duplicate_ids_are_errors(validator, files):
    report = run(validator, files, cases=[GOOD_CASE, dict(GOOD_CASE, title="Other")])
    assert any("duplicated test_case_id" in e for e in report.errors)


@pytest.mark.parametrize("tc_id", ["TC-1", "tc-login-001", "TEST-LOGIN-001", "TC-LOGIN-01"])
def test_malformed_test_ids(validator, files, tc_id):
    report = run(validator, files, cases=[dict(GOOD_CASE, test_case_id=tc_id)], rows=False)
    assert any("TC-<AREA>-<NNN>" in e for e in report.errors)


@pytest.mark.parametrize("column,value", [
    ("priority", "P1"), ("test_type", "Happy path"), ("automation", "Yes"),
])
def test_invalid_enums(validator, files, column, value):
    report = run(validator, files, cases=[dict(GOOD_CASE, **{column: value})], rows=False)
    assert any(f"'{column}' value '{value}'" in e for e in report.errors)


@pytest.mark.parametrize("column", ["title", "objective", "steps", "expected_result", "requirement_id"])
def test_required_values(validator, files, column):
    report = run(validator, files, cases=[dict(GOOD_CASE, **{column: ""})], rows=False)
    assert any(f"'{column}' is empty" in e for e in report.errors)


@pytest.mark.parametrize("vague", ["Works correctly", "as expected", "OK", "Funciona correctamente"])
def test_unverifiable_expected_results(validator, files, vague):
    report = run(validator, files, cases=[dict(GOOD_CASE, expected_result=vague)], rows=False)
    assert any("not verifiable" in e for e in report.errors)


def test_unknown_technique_is_warning(validator, files):
    report = run(validator, files, cases=[dict(GOOD_CASE, technique="Vibes")], rows=False)
    assert report.errors == []
    assert any("unknown technique" in w for w in report.warnings)


def test_matrix_references_unknown_test(validator, files):
    report = run(validator, files, rows=[dict(GOOD_ROW, test_case_ids="TC-LOGIN-001;TC-LOGIN-999")])
    assert any("unknown test case 'TC-LOGIN-999'" in e for e in report.errors)


def test_requirement_missing_from_matrix(validator, files):
    case = dict(GOOD_CASE, requirement_id="AC-1;AC-2")
    report = run(validator, files, cases=[case])
    assert any("'AC-2' is not in the traceability matrix" in e for e in report.errors)


def test_covered_without_tests_is_error_and_gap_is_allowed(validator, files):
    rows = [GOOD_ROW, dict(GOOD_ROW, requirement_id="AC-9", test_case_ids="", coverage_status="Covered")]
    assert any("status 'Covered' but no test_case_ids" in e for e in run(validator, files, rows=rows).errors)
    rows[1]["coverage_status"] = "Not covered"
    report = run(validator, files, rows=rows)
    assert report.errors == []
    assert report.summary["requirement_coverage"] == "1/2 (50%)"


def test_invalid_coverage_status(validator, files):
    report = run(validator, files, rows=[dict(GOOD_ROW, coverage_status="Done")])
    assert any("coverage_status 'Done'" in e for e in report.errors)


def test_link_inconsistency_is_warning(validator, files):
    rows = [dict(GOOD_ROW, test_case_ids="")]
    rows[0]["coverage_status"] = "Not covered"
    report = run(validator, files, rows=rows)
    assert any("not listed under requirement 'AC-1'" in w for w in report.warnings)


def test_missing_columns(validator, tmp_path):
    path = tmp_path / "cases.csv"
    path.write_text("test_case_id,title\nTC-A-001,x\n", encoding="utf-8")
    report = validator.validate(path)
    assert any("missing required column" in e for e in report.errors)


def test_secrets_are_detected_without_echoing_policy(validator, files):
    fake_aws = "AKIA" + "Z" * 16  # built at runtime so the repository scan stays clean
    report = run(validator, files, cases=[dict(GOOD_CASE, test_data=f"key={fake_aws}")], rows=False)
    assert any("AWS access key" in e for e in report.errors)


def test_placeholder_passwords_are_not_flagged(validator, files):
    for data in ("password=${API_PASSWORD}", "password=<wrong-password>", "password={{password}}"):
        report = run(validator, files, cases=[dict(GOOD_CASE, test_data=data)], rows=False)
        assert not any("password" in w for w in report.warnings), data


def test_literal_password_is_warning(validator, files):
    report = run(validator, files, cases=[dict(GOOD_CASE, test_data="pass" + "word=Sup3rS3cret")], rows=False)
    assert any("inline password" in w for w in report.warnings)


def test_bom_and_extra_values(validator, tmp_path):
    header = ",".join(validator.CASE_COLUMNS)
    values = ",".join(GOOD_CASE[c] for c in validator.CASE_COLUMNS)
    path = tmp_path / "bom.csv"
    path.write_text("﻿" + header + "\n" + values + ",unexpected\n", encoding="utf-8")
    report = validator.validate(path)
    assert any("more values than columns" in e for e in report.errors)
    assert not any("missing required column" in e for e in report.errors)


def _cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def test_cli_exit_codes_and_json(files, tmp_path):
    cases, matrix = files()
    ok = _cli(cases, "--traceability", matrix, "--json")
    assert ok.returncode == 0, ok.stderr
    assert json.loads(ok.stdout)["valid"] is True
    assert _cli(tmp_path / "missing.csv").returncode == 2


def test_cli_invalid_and_strict(validator, files):
    cases, _ = files(cases=[dict(GOOD_CASE, priority="P1")], rows=False)
    assert _cli(cases).returncode == 1
    cases, _ = files(cases=[dict(GOOD_CASE, technique="Vibes")], rows=False)
    assert _cli(cases).returncode == 0
    assert _cli(cases, "--strict").returncode == 1
