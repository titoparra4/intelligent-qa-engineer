# Customers API — local mock

[`server.py`](server.py) is a deterministic implementation of
[`../openapi/customers-api.yaml`](../openapi/customers-api.yaml). It is
used by the pytest and Postman examples.

- Uses only the Python standard library (3.9+).
- Keeps all data in memory. The data resets on every start.
- Binds to `127.0.0.1` by default. **Do not expose it on a network.**

```bash
python examples/mock-api/server.py --port 8000
curl http://127.0.0.1:8000/health
curl -H "Authorization: Bearer local-user-token" http://127.0.0.1:8000/customers
```

## Demo tokens

These are fake, non-secret values. They are accepted only by this mock.

| Role | Default value | Override |
|---|---|---|
| user | `local-user-token` | `MOCK_API_USER_TOKEN` |
| admin | `local-admin-token` | `MOCK_API_ADMIN_TOKEN` |
| expired | `local-expired-token` | — (always returns `401 token_expired`) |

Set `MOCK_API_VERBOSE=1` to log requests.

## Behavior outside the contract

These responses exist in the mock but are not documented in the contract.
They are deliberate, so that the "contract gap" findings in Example 2 have
something concrete behind them:

- `413` for bodies larger than 64 KiB;
- `405` for unsupported methods;
- `500` as a safety net.
