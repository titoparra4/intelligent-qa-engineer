#!/usr/bin/env python3
"""Scan repository files for credentials using the skill validator's patterns.

    python tools/scan_secrets.py            # scan git-tracked + untracked, non-ignored files
    python tools/scan_secrets.py path ...   # scan specific files/directories

High-confidence patterns fail the scan (exit 1); low-confidence patterns are
reported as warnings. The demo tokens of the local mock (local-*-token) are
intentionally fake and do not match any pattern.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "skills" / "intelligent-qa-engineer" / "scripts" / "validate_test_cases.py"
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "reports", "dist"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".zip", ".pdf", ".ico", ".pyc"}


def _load_patterns():
    spec = importlib.util.spec_from_file_location("qa_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module  # dataclasses need the module registered
    sys.dont_write_bytecode = True   # keep the skill folder free of __pycache__
    spec.loader.exec_module(module)
    return module.SECRET_PATTERNS, module.SUSPICIOUS_PATTERNS


def _candidate_files(paths: Sequence[str]) -> Iterable[Path]:
    if paths:
        for raw in paths:
            path = Path(raw)
            if path.is_dir():
                yield from (p for p in path.rglob("*") if p.is_file() and not SKIP_DIRS & set(p.parts))
            elif path.is_file():
                yield path
        return
    try:
        out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
        for line in out.splitlines():
            path = ROOT / line
            if path.is_file():
                yield path
    except (OSError, subprocess.CalledProcessError):
        yield from (p for p in ROOT.rglob("*") if p.is_file() and not SKIP_DIRS & set(p.relative_to(ROOT).parts))


def scan(paths: Sequence[str] = ()) -> tuple:
    secrets, suspicious = _load_patterns()
    errors: List[str] = []
    warnings: List[str] = []
    for path in _candidate_files(paths):
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            for label, pattern in secrets.items():
                if pattern.search(line):
                    errors.append(f"{path}:{number}: possible {label}")
            for label, pattern in suspicious.items():
                if pattern.search(line):
                    warnings.append(f"{path}:{number}: {label} (verify it is fake)")
    return errors, warnings


def main(argv: Sequence[str] = ()) -> int:
    errors, warnings = scan(argv)
    for message in errors:
        print(f"ERROR   {message}")
    for message in warnings:
        print(f"WARNING {message}")
    print(f"Result: {'FOUND SECRETS' if errors else 'CLEAN'} ({len(errors)} error(s), {len(warnings)} warning(s))")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
