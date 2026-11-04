"""POST /customers: validation, business rules BR-1/BR-3/BR-5 and payload handling."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from api_helpers import describe


def _post(api, token, payload, **kwargs):
    return api.post("/customers", token=token, json=payload, **kwargs)


def _assert_validation_error(response, assert_schema, field):
    assert response.status_code == 422, describe(response)
    body = response.json()
    assert_schema(body, "Error")
    assert body["error"]["code"] == "validation_error"
    assert field in [d["field"] for d in body["error"]["details"]], body


@pytest.mark.smoke
@pytest.mark.contract
def test_create_with_required_fields_applies_defaults(api, user_token, admin_token, unique_email, assert_schema):
    """TC-CUS-002: minimal valid payload -> 201, defaults applied, Location header, schema valid."""
    email = unique_email()
    response = _post(api, user_token, {"name": "  Ada Lovelace  ", "email": email})
    assert response.status_code == 201, describe(response)
    body = response.json()
    assert_schema(body, "Customer")
    assert body["name"] == "Ada Lovelace", "name must be trimmed"
    assert body["email"] == email
    assert body["status"] == "active"
    assert body["credit_limit"] == 0
    assert response.headers["Location"] == f"/customers/{body['id']}"
    follow_up = api.get(f"/customers/{body['id']}", token=user_token)
    assert follow_up.status_code == 200 and follow_up.json() == body
    api.delete(f"/customers/{body['id']}", token=admin_token)


@pytest.mark.parametrize("credit_limit", [0, 1, 49999, 50000])
def test_create_accepts_credit_limit_boundaries(create_customer, credit_limit):
    """TC-CUS-003: credit_limit boundaries inside [0, 50000] are accepted (BVA)."""
    customer = create_customer(credit_limit=credit_limit, status="suspended")
    assert customer["credit_limit"] == credit_limit
    assert customer["status"] == "suspended"


@pytest.mark.negative
@pytest.mark.parametrize("credit_limit", [-1, 50001])
def test_create_rejects_credit_limit_out_of_range(api, user_token, unique_email, assert_schema, credit_limit):
    """TC-CUS-004: credit_limit -1 and 50001 are rejected with 422 (BVA)."""
    response = _post(api, user_token, {"name": "QA", "email": unique_email(), "credit_limit": credit_limit})
    _assert_validation_error(response, assert_schema, "credit_limit")


@pytest.mark.negative
@pytest.mark.parametrize("credit_limit", ["100", 10.5, True, None])
def test_create_rejects_non_integer_credit_limit(api, user_token, unique_email, assert_schema, credit_limit):
    """TC-CUS-005: string, decimal, boolean and null credit_limit are rejected with 422 (EP)."""
    response = _post(api, user_token, {"name": "QA", "email": unique_email(), "credit_limit": credit_limit})
    _assert_validation_error(response, assert_schema, "credit_limit")


@pytest.mark.negative
@pytest.mark.parametrize("missing", ["name", "email"])
def test_create_rejects_missing_required_field(api, user_token, unique_email, assert_schema, missing):
    """TC-CUS-006: each required field missing (one at a time) -> 422 naming the field."""
    payload = {"name": "QA", "email": unique_email()}
    del payload[missing]
    _assert_validation_error(_post(api, user_token, payload), assert_schema, missing)


@pytest.mark.negative
@pytest.mark.parametrize("name", ["", "   ", "x" * 101, 123])
def test_create_rejects_invalid_name(api, user_token, unique_email, assert_schema, name):
    """TC-CUS-007: blank, whitespace-only, 101-char and non-string names are rejected."""
    _assert_validation_error(_post(api, user_token, {"name": name, "email": unique_email()}), assert_schema, "name")


def test_create_accepts_name_at_max_length(create_customer):
    """TC-CUS-007: a 100-character name (upper boundary) is accepted."""
    assert len(create_customer(name="x" * 100)["name"]) == 100


@pytest.mark.negative
@pytest.mark.parametrize("email", ["plainaddress", "no-at.example.test", "a@b", "a b@example.test", "", 42])
def test_create_rejects_invalid_email(api, user_token, assert_schema, email):
    """TC-CUS-008: malformed or non-string emails are rejected with 422."""
    _assert_validation_error(_post(api, user_token, {"name": "QA", "email": email}), assert_schema, "email")


@pytest.mark.negative
@pytest.mark.parametrize("status", ["closed", "ACTIVE", "deleted"])
def test_create_rejects_disallowed_status(api, user_token, unique_email, assert_schema, status):
    """TC-CUS-009: customers cannot be created as closed or with unknown/miscased status."""
    response = _post(api, user_token, {"name": "QA", "email": unique_email(), "status": status})
    _assert_validation_error(response, assert_schema, "status")


@pytest.mark.negative
@pytest.mark.parametrize("field", ["id", "role", "is_admin"])
def test_create_rejects_unknown_fields(api, user_token, unique_email, assert_schema, field):
    """TC-CUS-010: unknown fields (additionalProperties: false) are rejected, including privilege-like fields."""
    response = _post(api, user_token, {"name": "QA", "email": unique_email(), field: "x"})
    _assert_validation_error(response, assert_schema, field)


@pytest.mark.negative
@pytest.mark.parametrize("raw", ['{"name": "QA", "email": ', "", "[]", '"text"'])
def test_create_rejects_malformed_json(api, user_token, assert_schema, raw):
    """TC-CUS-011: malformed JSON, empty body and non-object JSON return 400 malformed_json."""
    response = api.post("/customers", token=user_token, data=raw, headers={"Content-Type": "application/json"})
    assert response.status_code == 400, describe(response)
    assert_schema(response.json(), "Error")
    assert response.json()["error"]["code"] == "malformed_json"


@pytest.mark.negative
@pytest.mark.parametrize("content_type", ["text/plain", "application/x-www-form-urlencoded"])
def test_create_rejects_unsupported_media_type(api, user_token, content_type):
    """TC-CUS-012: non-JSON Content-Type returns 415."""
    response = api.post("/customers", token=user_token, data="name=QA", headers={"Content-Type": content_type})
    assert response.status_code == 415, describe(response)
    assert response.json()["error"]["code"] == "unsupported_media_type"


@pytest.mark.negative
def test_create_rejects_duplicate_email_case_insensitive(api, user_token, create_customer, assert_schema):
    """TC-CUS-013: BR-1 — the same email with different case returns 409 email_conflict."""
    existing = create_customer()
    response = _post(api, user_token, {"name": "Other", "email": existing["email"].upper()})
    assert response.status_code == 409, describe(response)
    assert_schema(response.json(), "Error")
    assert response.json()["error"]["code"] == "email_conflict"


def test_idempotent_retry_returns_original_without_duplicate(api, user_token, admin_token, unique_email):
    """TC-CUS-014: BR-5 — same Idempotency-Key + same body replays the 201 and creates nothing new."""
    key = f"idem-{unique_email()}"
    payload = {"name": "Idem", "email": unique_email()}
    first = _post(api, user_token, payload, headers={"Idempotency-Key": key})
    second = _post(api, user_token, payload, headers={"Idempotency-Key": key})
    assert first.status_code == 201, describe(first)
    assert second.status_code == 201, describe(second)
    assert second.json()["id"] == first.json()["id"]
    assert second.headers.get("Idempotent-Replayed") == "true"
    assert "Idempotent-Replayed" not in first.headers
    listing = api.get("/customers", token=user_token, params={"limit": 100}).json()
    assert [c["email"] for c in listing["data"]].count(payload["email"]) == 1
    api.delete(f"/customers/{first.json()['id']}", token=admin_token)


@pytest.mark.negative
def test_idempotency_key_reused_with_different_body(api, user_token, admin_token, unique_email):
    """TC-CUS-015: BR-5 — same Idempotency-Key with a different body returns 422 idempotency_key_reused."""
    key = f"idem-{unique_email()}"
    first = _post(api, user_token, {"name": "A", "email": unique_email()}, headers={"Idempotency-Key": key})
    second = _post(api, user_token, {"name": "B", "email": unique_email()}, headers={"Idempotency-Key": key})
    assert first.status_code == 201, describe(first)
    assert second.status_code == 422, describe(second)
    assert second.json()["error"]["code"] == "idempotency_key_reused"
    api.delete(f"/customers/{first.json()['id']}", token=admin_token)


@pytest.mark.negative
@pytest.mark.concurrency
def test_concurrent_creates_with_same_email_create_exactly_one(api, user_token, admin_token, unique_email):
    """TC-CUS-033: BR-1 under concurrency — parallel creates with one email yield one 201, the rest 409."""
    email = unique_email()
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(lambda i: _post(api, user_token, {"name": f"C{i}", "email": email}), range(8)))
    statuses = sorted(r.status_code for r in responses)
    assert statuses.count(201) == 1, statuses
    assert statuses.count(409) == 7, statuses
    created = next(r for r in responses if r.status_code == 201)
    api.delete(f"/customers/{created.json()['id']}", token=admin_token)
