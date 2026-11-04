"""Structure checks for the manual behavioral scenarios."""

from __future__ import annotations

from pathlib import Path

import yaml

from conftest import ROOT

SCENARIOS = Path(__file__).parent / "scenarios" / "scenarios.yaml"
REQUIRED_CATEGORIES = {
    "activation", "non-activation", "traceability", "negative-coverage", "automation",
    "incomplete-requirements", "regression", "reporting", "secrets", "no-tools",
    "prompt-injection", "bilingual",
}


def load():
    return yaml.safe_load(SCENARIOS.read_text(encoding="utf-8"))["scenarios"]


def test_scenarios_are_well_formed():
    scenarios = load()
    ids = [s["id"] for s in scenarios]
    assert len(ids) == len(set(ids))
    for scenario in scenarios:
        assert set(scenario) == {"id", "category", "language", "prompt", "fixtures", "expect", "must_not"}, scenario["id"]
        assert scenario["language"] in {"en", "es"}
        assert scenario["prompt"].strip()
        assert scenario["expect"], scenario["id"]
        assert isinstance(scenario["must_not"], list)


def test_every_validation_category_is_covered():
    assert REQUIRED_CATEGORIES <= {s["category"] for s in load()}


def test_both_languages_are_exercised():
    assert {s["language"] for s in load()} == {"en", "es"}


def test_fixtures_exist():
    for scenario in load():
        for fixture in scenario["fixtures"]:
            assert (ROOT / fixture).is_file(), f"{scenario['id']}: {fixture}"
