"""Shared helpers for repository tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "intelligent-qa-engineer"
EXAMPLES = ROOT / "examples"

sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def validator() -> ModuleType:
    return load_module("qa_validate_test_cases", SKILL_DIR / "scripts" / "validate_test_cases.py")


@pytest.fixture(scope="session")
def skill_validator() -> ModuleType:
    return load_module("qa_validate_skill", ROOT / "tools" / "validate_skill.py")


@pytest.fixture(scope="session")
def secret_scanner() -> ModuleType:
    return load_module("qa_scan_secrets", ROOT / "tools" / "scan_secrets.py")
