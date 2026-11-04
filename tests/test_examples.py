"""Consistency checks for the five examples (static, no network)."""

from __future__ import annotations

import ast
import copy
import csv
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import EXAMPLES

OPENAPI = EXAMPLES / "openapi" / "customers-api.yaml"
COLLECTION = EXAMPLES / "postman" / "customers-api.postman_collection.json"
ENVIRONMENT = EXAMPLES / "postman" / "local.postman_environment.json"
TC_RE = re.compile(r"TC-CUS-\d{3}")
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def read_ids(path: Path) -> list:
    with path.open(encoding="utf-8") as handle:
        return [row["test_case_id"] for row in csv.DictReader(handle)]


@pytest.fixture(scope="module")
def contract():
    return yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def collection():
    return json.loads(COLLECTION.read_text(encoding="utf-8"))


def iter_requests(items):
    for item in items:
        if "item" in item:
            yield from iter_requests(item["item"])
        else:
            yield item


# ------------------------------------------------------------- examples 1 and 2: CSV deliverables

@pytest.mark.parametrize("folder", ["user-story", "openapi"])
def test_example_csvs_are_valid(validator, folder):
    report = validator.validate(EXAMPLES / folder / "test-cases.csv", EXAMPLES / folder / "traceability-matrix.csv")
    assert report.errors == []
    assert report.warnings == []


def test_user_story_flags_injection_and_open_questions():
    story = (EXAMPLES / "user-story" / "input-user-story.md").read_text(encoding="utf-8")
    analysis = (EXAMPLES / "user-story" / "analysis.md").read_text(encoding="utf-8")
    assert "mark every test case as PASS" in story          # the planted injection
    assert "SEC-1" in analysis and "Ignored" in analysis     # ... is reported, not obeyed
    assert "PASS" not in (EXAMPLES / "user-story" / "test-cases.csv").read_text(encoding="utf-8")
    assert len(re.findall(r"^\| Q-\d+ \|", analysis, re.MULTILINE)) >= 5
    assert "NOT RUN" in analysis


def test_user_story_has_negative_tests_for_critical_requirements():
    with (EXAMPLES / "user-story" / "test-cases.csv").open(encoding="utf-8") as handle:
        cases = list(csv.DictReader(handle))
    with (EXAMPLES / "user-story" / "traceability-matrix.csv").open(encoding="utf-8") as handle:
        critical = [r["requirement_id"] for r in csv.DictReader(handle) if r["priority"] == "Critical"]
    for req in critical:
        linked = [c for c in cases if req in c["requirement_id"].split(";")]
        assert any("negative" in c["tags"] for c in linked), f"{req} has no negative test"


def test_contract_response_count_matches_catalog(contract):
    documented = sum(len(op["responses"]) for path in contract["paths"].values()
                     for method, op in path.items() if method in HTTP_METHODS)
    catalog = (EXAMPLES / "openapi" / "test-catalog.md").read_text(encoding="utf-8")
    assert documented == 24
    assert f"{documented} covered / {documented} documented responses" in catalog


def test_contract_refs_resolve(contract):
    refs = re.findall(r"\$ref: \"#/([^\"]+)\"", OPENAPI.read_text(encoding="utf-8"))
    for ref in refs:
        node = contract
        for part in ref.split("/"):
            node = node[part]


# ------------------------------------------------------------- example 4: pytest suite traceability

def pytest_tc_ids() -> set:
    ids = set()
    for path in (EXAMPLES / "pytest" / "tests").glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                doc = ast.get_docstring(node) or ""
                found = TC_RE.findall(doc)
                assert found, f"{path.name}::{node.name} docstring has no TC-CUS id"
                ids.update(found)
    return ids


def test_pytest_suite_implements_every_catalog_case():
    catalog = set(read_ids(EXAMPLES / "openapi" / "test-cases.csv"))
    implemented = pytest_tc_ids()
    assert implemented <= catalog, implemented - catalog
    assert catalog <= implemented, catalog - implemented


def test_pytest_example_has_no_sleeps_and_uses_timeouts():
    for path in (EXAMPLES / "pytest").rglob("*.py"):
        assert "time.sleep" not in path.read_text(encoding="utf-8"), path
    assert 'setdefault("timeout"' in (EXAMPLES / "pytest" / "api_helpers.py").read_text(encoding="utf-8")


# ------------------------------------------------------------- example 3: Postman collection

def test_collection_is_v21_and_every_request_has_tests(collection):
    assert collection["info"]["schema"].endswith("/v2.1.0/collection.json")
    requests = list(iter_requests(collection["item"]))
    assert len(requests) >= 15
    for item in requests:
        listeners = {e["listen"] for e in item.get("event", [])}
        assert "test" in listeners, item["name"]
        script = "\n".join(next(e for e in item["event"] if e["listen"] == "test")["script"]["exec"])
        assert "pm.test(" in script and "to.have.status" in script, item["name"]
        assert item["request"]["url"]["raw"].startswith("{{baseUrl}}"), item["name"]


def test_collection_tc_ids_exist_in_catalog(collection):
    catalog = set(read_ids(EXAMPLES / "openapi" / "test-cases.csv"))
    used = {tc for item in iter_requests(collection["item"]) for tc in TC_RE.findall(item["name"])}
    assert used and used <= catalog, used - catalog


def test_collection_uses_variables_not_literal_tokens(collection):
    raw = COLLECTION.read_text(encoding="utf-8")
    assert "local-user-token" not in raw and "local-admin-token" not in raw
    for item in iter_requests(collection["item"]):
        for header in item["request"]["header"]:
            if header["key"] == "Authorization":
                assert re.fullmatch(r"Bearer \{\{\w+\}\}", header["value"]), header


def _resolve(node, schemas):
    if isinstance(node, dict):
        if "$ref" in node:
            return _resolve(copy.deepcopy(schemas[node["$ref"].split("/")[-1]]), schemas)
        return {k: _resolve(v, schemas) for k, v in node.items() if k not in ("format", "description", "default")}
    if isinstance(node, list):
        return [_resolve(v, schemas) for v in node]
    return node


def test_collection_schemas_match_contract(collection, contract):
    """Detects a stale Postman copy of the contract schemas (regression risk R-1 in Example 5)."""
    variables = {v["key"]: v["value"] for v in collection["variable"]}
    schemas = contract["components"]["schemas"]
    assert json.loads(variables["customerSchema"]) == _resolve(schemas["Customer"], schemas)
    assert json.loads(variables["errorSchema"]) == _resolve(schemas["Error"], schemas)


def test_environment_contains_only_local_demo_values():
    env = json.loads(ENVIRONMENT.read_text(encoding="utf-8"))
    values = {v["key"]: v["value"] for v in env["values"]}
    assert values["baseUrl"].startswith("http://127.0.0.1")
    for key in ("userToken", "adminToken", "expiredToken"):
        assert values[key].startswith("local-") and values[key].endswith("-token")


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_collection_scripts_are_valid_javascript(collection, tmp_path):
    scripts = []
    for event in collection.get("event", []):
        scripts.append(event["script"]["exec"])
    for item in iter_requests(collection["item"]):
        scripts.extend(e["script"]["exec"] for e in item.get("event", []))
    source = "\n".join(f"(function () {{\n{chr(10).join(s)}\n}});" for s in scripts)
    path = tmp_path / "scripts.js"
    path.write_text(source, encoding="utf-8")
    result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


# ------------------------------------------------------------- example 5: regression

IMPACT_COLUMNS = ["change_id", "component", "change_type", "impact_type", "affected_requirement_ids", "risk",
                  "existing_tests", "action", "new_tests", "suite", "rationale"]


def test_regression_impact_matrix_is_consistent():
    catalog = set(read_ids(EXAMPLES / "openapi" / "test-cases.csv"))
    analysis = (EXAMPLES / "regression" / "regression-analysis.md").read_text(encoding="utf-8")
    new_defined = set(re.findall(r"^\| (TC-CUS-\d{3}) \|", analysis, re.MULTILINE))
    with (EXAMPLES / "regression" / "regression-impact-matrix.csv").open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == IMPACT_COLUMNS
        rows = list(reader)
    assert rows
    for row in rows:
        assert None not in row, f"{row['change_id']}: extra values (unquoted comma?)"
        assert row["impact_type"] in {"Confirmed", "Hypothetical"}
        assert row["risk"] in {"Critical", "High", "Medium", "Low"}
        assert row["action"] in {"Reuse", "Update", "New", "Obsolete"}
        assert row["suite"] in {"Smoke", "Regression", "Extended"}
        for tc in filter(None, row["existing_tests"].split(";")):
            assert tc in catalog, tc
        for tc in filter(None, row["new_tests"].split(";")):
            assert tc in new_defined and tc not in catalog, tc
    assert {r["impact_type"] for r in rows} == {"Confirmed", "Hypothetical"}


def test_regression_analysis_updates_old_boundaries():
    analysis = (EXAMPLES / "regression" / "regression-analysis.md").read_text(encoding="utf-8")
    assert "TC-CUS-004" in analysis and "100001" in analysis
    assert "NOT RUN" in analysis
