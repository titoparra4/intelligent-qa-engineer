"""Shared fixtures for the Customers API pytest suite.

By default the suite starts the deterministic local mock
(examples/mock-api/server.py) on a random free port, so it needs no
network access and no credentials. Set API_BASE_URL to target another
environment; non-local hosts additionally require ALLOW_REMOTE_TESTS=1.
"""

from __future__ import annotations

import importlib.util
import os
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional
from urllib.parse import urlparse

import pytest
import yaml
from jsonschema import Draft7Validator, FormatChecker

from api_helpers import ApiClient, describe

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE.parent
CONTRACT = EXAMPLES / "openapi" / "customers-api.yaml"
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _load_mock() -> Any:
    """Import examples/mock-api/server.py under a collision-free module name."""
    spec = importlib.util.spec_from_file_location("customers_mock_server", EXAMPLES / "mock-api" / "server.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def target() -> Iterator[Dict[str, Any]]:
    base_url = os.environ.get("API_BASE_URL")
    server = None
    if base_url:
        host = urlparse(base_url).hostname or ""
        if host not in LOCAL_HOSTS and os.environ.get("ALLOW_REMOTE_TESTS") != "1":
            pytest.exit(f"Refusing to run against non-local host '{host}'. "
                        "Set ALLOW_REMOTE_TESTS=1 only if you are authorized to test it.", returncode=2)
        user_token = os.environ.get("API_USER_TOKEN")
        admin_token = os.environ.get("API_ADMIN_TOKEN")
        if not user_token or not admin_token:
            pytest.exit("API_USER_TOKEN and API_ADMIN_TOKEN must be set when API_BASE_URL is set.", returncode=2)
        local = host in LOCAL_HOSTS
    else:
        mock = _load_mock()
        server, base_url = mock.start_in_thread()
        user_token = os.environ.get("MOCK_API_USER_TOKEN", mock.DEFAULT_USER_TOKEN)
        admin_token = os.environ.get("MOCK_API_ADMIN_TOKEN", mock.DEFAULT_ADMIN_TOKEN)
        local = True
    yield {
        "base_url": base_url,
        "user_token": user_token,
        "admin_token": admin_token,
        "expired_token": os.environ.get("API_EXPIRED_TOKEN", "local-expired-token"),
        "local": local,
    }
    if server is not None:
        server.shutdown()
        server.server_close()


@pytest.fixture(autouse=True)
def _guard_destructive(request: pytest.FixtureRequest, target: Dict[str, Any]) -> None:
    if request.node.get_closest_marker("destructive") and not target["local"] \
            and os.environ.get("ALLOW_DESTRUCTIVE_TESTS") != "1":
        pytest.skip("destructive test skipped on non-local target (set ALLOW_DESTRUCTIVE_TESTS=1 to allow)")


@pytest.fixture(scope="session")
def api(target: Dict[str, Any]) -> ApiClient:
    return ApiClient(target["base_url"], float(os.environ.get("API_TIMEOUT_SECONDS", "5")))


@pytest.fixture(scope="session")
def user_token(target: Dict[str, Any]) -> str:
    return target["user_token"]


@pytest.fixture(scope="session")
def admin_token(target: Dict[str, Any]) -> str:
    return target["admin_token"]


@pytest.fixture(scope="session")
def expired_token(target: Dict[str, Any]) -> str:
    return target["expired_token"]


@pytest.fixture(scope="session")
def contract() -> Dict[str, Any]:
    with CONTRACT.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@pytest.fixture(scope="session")
def assert_schema(contract: Dict[str, Any]) -> Callable[[Any, str], None]:
    """Validate a JSON body against components/schemas/<name> of the contract."""

    def _assert(instance: Any, schema_name: str) -> None:
        schema = {"$ref": f"#/components/schemas/{schema_name}", "components": contract["components"]}
        errors = sorted(Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
                        key=lambda e: list(e.path))
        assert not errors, f"{schema_name} schema violations: " + "; ".join(
            f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors)

    return _assert


@pytest.fixture
def unique_email() -> Callable[[], str]:
    return lambda: f"qa-{uuid.uuid4().hex[:12]}@example.test"


@pytest.fixture
def create_customer(api: ApiClient, user_token: str, admin_token: str,
                    unique_email: Callable[[], str]) -> Iterator[Callable[..., Dict[str, Any]]]:
    """Factory that creates a customer with unique data and deletes it afterwards."""
    created: List[str] = []

    def _create(**overrides: Any) -> Dict[str, Any]:
        payload = {"name": "QA Customer", "email": unique_email(), **overrides}
        response = api.post("/customers", token=user_token, json=payload)
        assert response.status_code == 201, describe(response)
        body = response.json()
        created.append(body["id"])
        return body

    yield _create
    for customer_id in created:  # best-effort cleanup; 404 means a test already deleted it
        api.delete(f"/customers/{customer_id}", token=admin_token)
