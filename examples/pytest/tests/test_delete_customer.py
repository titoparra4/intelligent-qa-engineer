"""DELETE /customers/{id}: BR-4 admin-only deletion."""

import pytest

from api_helpers import describe


@pytest.mark.destructive
def test_admin_can_delete_customer(api, user_token, admin_token, create_customer):
    """TC-CUS-030: admin DELETE returns 204 and the customer is gone afterwards."""
    customer = create_customer()
    response = api.delete(f"/customers/{customer['id']}", token=admin_token)
    assert response.status_code == 204, describe(response)
    assert response.content == b""
    assert api.get(f"/customers/{customer['id']}", token=user_token).status_code == 404


@pytest.mark.negative
def test_non_admin_cannot_delete_customer(api, user_token, create_customer, assert_schema):
    """TC-CUS-031: BR-4 — a user token returns 403 forbidden and the customer still exists."""
    customer = create_customer()
    response = api.delete(f"/customers/{customer['id']}", token=user_token)
    assert response.status_code == 403, describe(response)
    assert_schema(response.json(), "Error")
    assert response.json()["error"]["code"] == "forbidden"
    assert api.get(f"/customers/{customer['id']}", token=user_token).status_code == 200


@pytest.mark.negative
def test_delete_unknown_customer_returns_404(api, admin_token):
    """TC-CUS-032: DELETE on an unknown id returns 404 not_found."""
    response = api.delete("/customers/cus_999999", token=admin_token)
    assert response.status_code == 404, describe(response)
    assert response.json()["error"]["code"] == "not_found"
