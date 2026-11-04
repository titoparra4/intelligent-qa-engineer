"""Static validation of the skill package (Agent Skills spec + portability rules)."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest
import yaml

from conftest import SKILL_DIR

SKILL_MD = SKILL_DIR / "SKILL.md"
MODES = ["ANALYZE", "STRATEGY", "GENERATE", "NEGATIVE", "AUTOMATE", "REGRESSION", "COVERAGE", "REPORT", "FULL-QA"]


def frontmatter() -> dict:
    text = SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    return yaml.safe_load(text.split("---\n", 2)[1])


def body() -> str:
    return SKILL_MD.read_text(encoding="utf-8").split("---\n", 2)[2]


def test_real_skill_is_valid(skill_validator):
    result = skill_validator.validate_skill(SKILL_DIR)
    assert result["errors"] == []
    assert result["warnings"] == []
    assert result["valid"] is True


def test_frontmatter_required_fields_and_limits():
    meta = frontmatter()
    assert meta["name"] == "intelligent-qa-engineer" == SKILL_DIR.name
    assert 80 <= len(meta["description"]) <= 1024
    assert len(meta["compatibility"]) <= 500
    assert meta["license"] == "MIT"
    assert all(isinstance(v, str) for v in meta["metadata"].values())


@pytest.mark.parametrize("keyword", [
    "test cases", "OpenAPI", "regression", "coverage", "Postman", "pytest",
    "negative", "traceability", "QA", "Spanish", "Do not use",
])
def test_description_supports_discovery(keyword):
    """The description is the only text agents see before activation (validation item 1/2)."""
    assert keyword.lower() in frontmatter()["description"].lower()


def test_all_modes_are_documented_with_a_reference():
    text = body()
    for mode in MODES:
        assert re.search(rf"^\| {re.escape(mode)} \|", text, re.MULTILINE), f"mode {mode} missing from table"


def test_every_reference_is_linked_and_exists():
    text = body()
    references = sorted(p.name for p in (SKILL_DIR / "references").glob("*.md"))
    assert len(references) >= 8
    for name in references:
        assert f"references/{name}" in text, f"{name} not linked from SKILL.md"


@pytest.mark.parametrize("phrase", [
    "data, not instructions",       # prompt-injection rule
    "Never say a test passed",      # no false execution claims
    "NOT RUN",
    "explicit user authorization",  # production / destructive guard
    "credentials",                  # secrets rule
    "Analysis mode",                # no-tools behaviour
    "user's language",              # bilingual
    "Never invent requirements",
    "Requirement coverage is not code coverage",
])
def test_core_and_safety_rules_present(phrase):
    assert phrase.lower() in body().lower()


def test_templates_match_validator_columns(validator):
    templates = SKILL_DIR / "assets" / "templates"
    with (templates / "test-cases.csv").open(encoding="utf-8") as handle:
        assert next(csv.reader(handle)) == validator.CASE_COLUMNS
    with (templates / "traceability-matrix.csv").open(encoding="utf-8") as handle:
        assert next(csv.reader(handle)) == validator.MATRIX_COLUMNS
    for name in ("test-strategy.md", "qa-report.md", "regression-impact-matrix.csv"):
        assert (templates / name).is_file()


def test_templates_pass_validator(validator):
    templates = SKILL_DIR / "assets" / "templates"
    report = validator.validate(templates / "test-cases.csv", templates / "traceability-matrix.csv")
    assert report.errors == [] and report.warnings == []


def test_skill_md_documents_column_names_consistently(validator):
    text = body()
    for column in validator.CASE_COLUMNS:
        assert f"`{column}`" in text


def test_skill_folder_contains_only_portable_content():
    allowed_top = {"SKILL.md", "references", "assets", "scripts"}
    assert {p.name for p in SKILL_DIR.iterdir() if p.name != "__pycache__"} <= allowed_top


# ---------------------------------------------------------------- negative tests for the skill validator

def make_skill(tmp_path: Path, name: str = "demo-skill", meta: str = None, body_text: str = "# Demo\n") -> Path:
    skill = tmp_path / name
    skill.mkdir()
    meta = meta if meta is not None else (
        f"name: {name}\ndescription: Demo skill that validates things. Use when testing the validator itself.\n")
    (skill / "SKILL.md").write_text(f"---\n{meta}---\n{body_text}", encoding="utf-8")
    return skill


def errors_for(skill_validator, skill: Path) -> str:
    return "\n".join(skill_validator.validate_skill(skill)["errors"])


def test_validator_accepts_minimal_skill(skill_validator, tmp_path):
    assert skill_validator.validate_skill(make_skill(tmp_path))["valid"]


@pytest.mark.parametrize("bad_name", ["Demo-Skill", "-demo", "demo-", "demo--skill", "demo_skill"])
def test_validator_rejects_bad_names(skill_validator, tmp_path, bad_name):
    skill = make_skill(tmp_path, name=bad_name, meta=f"name: {bad_name}\ndescription: {'x' * 100}\n")
    assert "name must use" in errors_for(skill_validator, skill)


def test_validator_rejects_name_directory_mismatch(skill_validator, tmp_path):
    skill = make_skill(tmp_path, meta=f"name: other-name\ndescription: {'x' * 100}\n")
    assert "must match directory name" in errors_for(skill_validator, skill)


def test_validator_rejects_missing_or_long_description(skill_validator, tmp_path):
    missing_dir, long_dir = tmp_path / "missing", tmp_path / "long"
    missing_dir.mkdir()
    long_dir.mkdir()
    missing = make_skill(missing_dir, meta="name: demo-skill\n")
    long = make_skill(long_dir, meta=f"name: demo-skill\ndescription: {'x' * 1025}\n")
    assert "'description' is required" in errors_for(skill_validator, missing)
    assert "max 1024" in errors_for(skill_validator, long)


def test_validator_rejects_non_portable_fields(skill_validator, tmp_path):
    skill = make_skill(tmp_path, meta=f"name: demo-skill\ndescription: {'x' * 100}\ncontext: fork\n")
    assert "non-portable" in errors_for(skill_validator, skill)


def test_validator_rejects_non_string_metadata(skill_validator, tmp_path):
    skill = make_skill(tmp_path, meta=f"name: demo-skill\ndescription: {'x' * 100}\nmetadata:\n  version: 1.0\n")
    assert "metadata" in errors_for(skill_validator, skill)


def test_validator_rejects_missing_frontmatter(skill_validator, tmp_path):
    skill = tmp_path / "demo-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# No frontmatter\n", encoding="utf-8")
    assert "frontmatter" in errors_for(skill_validator, skill)


def test_validator_rejects_broken_and_escaping_links(skill_validator, tmp_path):
    (tmp_path / "outside.md").write_text("x", encoding="utf-8")
    skill = make_skill(tmp_path, body_text="[a](references/missing.md)\n[b](../outside.md)\n")
    errors = errors_for(skill_validator, skill)
    assert "broken link 'references/missing.md'" in errors
    assert "outside the skill directory" in errors


def test_validator_ignores_links_in_code(skill_validator, tmp_path):
    skill = make_skill(tmp_path, body_text="```\n[a](missing.md)\n```\nInline `[b](missing.md)`\n")
    assert skill_validator.validate_skill(skill)["valid"]


def test_validator_rejects_oversized_skill_md(skill_validator, tmp_path):
    skill = make_skill(tmp_path, body_text="line\n" * 600)
    assert "lines" in errors_for(skill_validator, skill)


def test_validator_rejects_absolute_paths_and_bad_scripts(skill_validator, tmp_path):
    skill = make_skill(tmp_path, body_text="See " + "/Users" + "/someone/secret/file\n")
    (skill / "scripts").mkdir()
    (skill / "scripts" / "broken.py").write_text("def (:\n", encoding="utf-8")
    errors = errors_for(skill_validator, skill)
    assert "absolute local path" in errors
    assert "does not compile" in errors


def test_validator_cli_exit_codes(skill_validator, tmp_path, capsys):
    assert skill_validator.main([str(SKILL_DIR)]) == 0
    assert skill_validator.main([str(make_skill(tmp_path, meta="name: demo-skill\n"))]) == 1
    assert skill_validator.main([str(tmp_path / "nope")]) == 2
