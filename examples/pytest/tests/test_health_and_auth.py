"""Health check and authentication (SEC-AUTH) across all protected operations."""

import pytest

from api_helpers import describe

PROTECTED_OPERATIONS = [
    ("GET", "/customers", None),
    ("POST", "/customers", {"name": "QA", "email": "auth-check@example.test"}),
    ("GET", "/customers/cus_000001", None),
    ("PATCH", "/customers/cus_000001", {"name": "QA"}),
    ("DELETE", "/customers/cus_000001", None),
]


@pytest.mark.smoke
@pytest.mark.contract
def test_health_returns_ok(api):
    """TC-CUS-001: GET /health returns 200 {"status": "ok"} without authentication."""
    response = api.get("/health")
    assert response.status_code == 200, describe(response)
    assert response.json() == {"status": "ok"}


@pytest.mark.negative
@pytest.mark.parametrize("method,path,body", PROTECTED_OPERATIONS)
def test_missing_token_is_rejected(api, assert_schema, method, path, body):
    """TC-CUS-016: every protected operation returns 401 + WWW-Authenticate without a token."""
    response = api.request(method, path, json=body)
    assert response.status_code == 401, describe(response)
    assert response.headers.get("WWW-Authenticate", "").startswith("Bearer")
    assert response.json()["error"]["code"] == "unauthorized"
    assert_schema(response.json(), "Error")


@pytest.mark.negative
@pytest.mark.parametrize("header", ["Bearer not-a-real-token", "Basic dXNlcjpwYXNz", "Bearer", "local-user-token"])
def test_invalid_or_malformed_token_is_rejected(api, header):
    """TC-CUS-017: invalid or malformed Authorization headers return 401 unauthorized."""
    response = api.get("/customers", headers={"Authorization": header})
    assert response.status_code == 401, describe(response)
    assert response.json()["error"]["code"] == "unauthorized"


@pytest.mark.negative
def test_expired_token_is_rejected(api, expired_token):
    """TC-CUS-018: an expired token returns 401 with code token_expired."""
    response = api.get("/customers", token=expired_token)
    assert response.status_code == 401, describe(response)
    assert response.json()["error"]["code"] == "token_expired"
