# Simulated PR #42 — "Raise credit limits, freeze suspended accounts, add phone"

> Simulated input for Example 5. The repository's mock API and contract
> stay at v1.0.0; this PR describes the proposed v1.1.0.

## Description (as written by the author)

- Raise the maximum `credit_limit` from 50000 to 100000 (marketing request MKT-88).
- New rule: the `credit_limit` of a **suspended** customer cannot be increased.
  The API returns `409` with error code `credit_limit_frozen`.
- Add an optional `phone` field (E.164 format) to customers.
- "Small refactor of the shared validation helper, no behaviour change."

## Files changed

| File | Change |
|---|---|
| `openapi/customers-api.yaml` | See [openapi-v1.1.diff](openapi-v1.1.diff) |
| `src/customers/validation.py` | `validate_fields()` — new limit constant, phone pattern; shared by create and update |
| `src/customers/service.py` | `update_customer()` — new suspended/credit check before applying changes |
| `src/customers/serializers.py` | Adds `phone` to the response representation |
