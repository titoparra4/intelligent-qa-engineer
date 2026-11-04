"""PATCH /customers/{id}: partial updates and the BR-2 status lifecycle."""

import pytest

from api_helpers import describe


def _patch(api, token, customer_id, payload):
    return api.patch(f"/customers/{customer_id}", token=token, json=payload)


def test_partial_update_changes_only_given_fields(api, user_token, create_customer, assert_schema):
    """TC-CUS-024: PATCH name only -> 200; other fields unchanged; schema valid."""
    customer = create_customer(credit_limit=500)
    response = _patch(api, user_token, customer["id"], {"name": "Renamed"})
    assert response.status_code == 200, describe(response)
    body = response.json()
    assert_schema(body, "Customer")
    assert body["name"] == "Renamed"
    for unchanged in ("email", "status", "credit_limit", "created_at"):
        assert body[unchanged] == customer[unchanged], unchanged


@pytest.mark.parametrize("path", [
    ["suspended", "active"],
    ["suspended", "closed"],
    ["closed"],
])
def test_valid_status_transitions(api, user_token, create_customer, path):
    """TC-CUS-025: BR-2 valid transitions active->suspended->active, suspended->closed, active->closed."""
    customer = create_customer()
    for status in path:
        response = _patch(api, user_token, customer["id"], {"status": status})
        assert response.status_code == 200, describe(response)
        assert response.json()["status"] == status


@pytest.mark.negative
@pytest.mark.parametrize("payload", [{"status": "active"}, {"status": "suspended"}, {"name": "Reopened"}])
def test_closed_customer_cannot_be_modified(api, user_token, create_customer, assert_schema, payload):
    """TC-CUS-026: BR-2 closed is terminal — any change returns 409 invalid_state_transition."""
    customer = create_customer()
    assert _patch(api, user_token, customer["id"], {"status": "closed"}).status_code == 200
    response = _patch(api, user_token, customer["id"], payload)
    assert response.status_code == 409, describe(response)
    assert_schema(response.json(), "Error")
    assert response.json()["error"]["code"] == "invalid_state_transition"
    assert api.get(f"/customers/{customer['id']}", token=user_token).json()["status"] == "closed"


@pytest.mark.negative
def test_update_with_empty_body_is_rejected(api, user_token, create_customer):
    """TC-CUS-027: an empty JSON object returns 422 (minProperties: 1)."""
    customer = create_customer()
    response = _patch(api, user_token, customer["id"], {})
    assert response.status_code == 422, describe(response)
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.negative
def test_update_email_to_existing_email_conflicts(api, user_token, create_customer):
    """TC-CUS-028: BR-1 — changing email to another customer's email (different case) returns 409."""
    first, second = create_customer(), create_customer()
    response = _patch(api, user_token, second["id"], {"email": first["email"].upper()})
    assert response.status_code == 409, describe(response)
    assert response.json()["error"]["code"] == "email_conflict"


def test_update_email_to_own_email_with_new_case_is_allowed(api, user_token, create_customer):
    """TC-CUS-028: BR-1 — re-casing a customer's own email is not a conflict."""
    customer = create_customer()
    response = _patch(api, user_token, customer["id"], {"email": customer["email"].upper()})
    assert response.status_code == 200, describe(response)


@pytest.mark.negative
def test_update_unknown_customer_returns_404(api, user_token):
    """TC-CUS-029: PATCH on an unknown id returns 404 not_found."""
    response = _patch(api, user_token, "cus_999999", {"name": "Ghost"})
    assert response.status_code == 404, describe(response)
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.negative
@pytest.mark.parametrize("credit_limit", [-1, 50001])
def test_update_rejects_credit_limit_out_of_range(api, user_token, create_customer, credit_limit):
    """TC-CUS-034: BR-3 applies to updates — -1 and 50001 return 422; value unchanged."""
    customer = create_customer(credit_limit=100)
    response = _patch(api, user_token, customer["id"], {"credit_limit": credit_limit})
    assert response.status_code == 422, describe(response)
    assert api.get(f"/customers/{customer['id']}", token=user_token).json()["credit_limit"] == 100


@pytest.mark.negative
def test_update_rejects_malformed_json_and_media_type(api, user_token, create_customer):
    """TC-CUS-035: PATCH with malformed JSON returns 400; with text/plain returns 415."""
    customer = create_customer()
    path = f"/customers/{customer['id']}"
    malformed = api.patch(path, token=user_token, data="{bad", headers={"Content-Type": "application/json"})
    assert malformed.status_code == 400, describe(malformed)
    wrong_type = api.patch(path, token=user_token, data="name=x", headers={"Content-Type": "text/plain"})
    assert wrong_type.status_code == 415, describe(wrong_type)
