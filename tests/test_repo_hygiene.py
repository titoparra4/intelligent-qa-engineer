"""Repository-level checks: required files, links, secrets, absolute paths."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import ROOT

SKIP = {".git", ".venv", "venv", "node_modules", ".pytest_cache", "__pycache__", "reports"}
REQUIRED = [
    "README.md", "README.es.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", ".gitignore",
    "docs/installation.md", "docs/validation-report.md",
    ".github/workflows/ci.yml", ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml", ".github/pull_request_template.md",
]


def repo_files(suffixes):
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in suffixes and not SKIP & set(path.relative_to(ROOT).parts):
            yield path


@pytest.mark.parametrize("name", REQUIRED)
def test_required_files_exist(name):
    assert (ROOT / name).is_file(), name


def test_license_is_mit():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert text.startswith("MIT License") and "Permission is hereby granted, free of charge" in text


def test_all_markdown_links_resolve(skill_validator):
    errors = skill_validator.check_markdown_links(sorted(repo_files({".md"})))
    assert errors == []


def test_no_secrets_in_repository(secret_scanner):
    files = [str(p) for p in repo_files({".md", ".py", ".json", ".yaml", ".yml", ".csv", ".sh", ".txt", ".diff"})]
    errors, warnings = secret_scanner.scan(files)
    assert errors == []
    assert warnings == []


def test_no_absolute_local_paths():
    pattern = re.compile(r"/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/")
    offenders = [str(p.relative_to(ROOT)) for p in repo_files({".md", ".py", ".json", ".yaml", ".yml", ".csv", ".sh"})
                 if pattern.search(p.read_text(encoding="utf-8")) and p.name != "test_repo_hygiene.py"
                 and p.name != "validate_skill.py"]
    assert offenders == []


def test_readme_does_not_invent_badges_or_metrics():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "shields.io" not in readme and "img.shields" not in readme
    assert not re.search(r"\b\d+[kK]?\+? (users|downloads|stars)\b", readme)
