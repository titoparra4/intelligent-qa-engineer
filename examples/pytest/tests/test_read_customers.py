"""GET /customers and GET /customers/{id}."""

import pytest

from api_helpers import describe


@pytest.mark.smoke
@pytest.mark.contract
def test_get_existing_customer(api, user_token, create_customer, assert_schema):
    """TC-CUS-019: GET an existing customer returns 200 and the Customer schema."""
    customer = create_customer()
    response = api.get(f"/customers/{customer['id']}", token=user_token)
    assert response.status_code == 200, describe(response)
    assert_schema(response.json(), "Customer")
    assert response.json() == customer


@pytest.mark.negative
@pytest.mark.parametrize("customer_id", ["cus_999999", "does-not-exist"])
def test_get_unknown_customer_returns_404(api, user_token, assert_schema, customer_id):
    """TC-CUS-020: unknown or malformed ids return 404 not_found."""
    response = api.get(f"/customers/{customer_id}", token=user_token)
    assert response.status_code == 404, describe(response)
    assert_schema(response.json(), "Error")
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.contract
def test_list_is_paginated_and_ordered(api, user_token, create_customer, assert_schema):
    """TC-CUS-021: list returns CustomerList ordered by id with consistent pagination metadata."""
    for _ in range(3):
        create_customer()
    response = api.get("/customers", token=user_token, params={"limit": 2, "offset": 0})
    assert response.status_code == 200, describe(response)
    body = response.json()
    assert_schema(body, "CustomerList")
    assert body["pagination"]["limit"] == 2
    assert body["pagination"]["offset"] == 0
    assert body["pagination"]["total"] >= 3
    assert len(body["data"]) == 2
    ids = [c["id"] for c in body["data"]]
    assert ids == sorted(ids)
    beyond = api.get("/customers", token=user_token, params={"offset": body["pagination"]["total"]}).json()
    assert beyond["data"] == []


def test_list_filters_by_status(api, user_token, create_customer):
    """TC-CUS-022: status filter returns only customers with that status."""
    suspended = create_customer(status="suspended")
    create_customer(status="active")
    response = api.get("/customers", token=user_token, params={"status": "suspended", "limit": 100})
    assert response.status_code == 200, describe(response)
    data = response.json()["data"]
    assert data and all(c["status"] == "suspended" for c in data)
    assert suspended["id"] in [c["id"] for c in data]


@pytest.mark.negative
@pytest.mark.parametrize("params,field", [
    ({"limit": 0}, "limit"),
    ({"limit": 101}, "limit"),
    ({"limit": "abc"}, "limit"),
    ({"offset": -1}, "offset"),
    ({"status": "deleted"}, "status"),
])
def test_list_rejects_invalid_query(api, user_token, assert_schema, params, field):
    """TC-CUS-023: limit outside [1,100], negative offset and unknown status return 422."""
    response = api.get("/customers", token=user_token, params=params)
    assert response.status_code == 422, describe(response)
    assert_schema(response.json(), "Error")
    assert field in [d["field"] for d in response.json()["error"]["details"]]


@pytest.mark.parametrize("limit", [1, 100])
def test_list_accepts_limit_boundaries(api, user_token, limit):
    """TC-CUS-023: limit boundaries 1 and 100 are accepted."""
    response = api.get("/customers", token=user_token, params={"limit": limit})
    assert response.status_code == 200, describe(response)
    assert response.json()["pagination"]["limit"] == limit
