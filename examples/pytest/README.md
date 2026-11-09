# Example 4 — Python automation (pytest)

This is a runnable API test suite for the Customers API, generated from
[`../openapi/customers-api.yaml`](../openapi/customers-api.yaml).

- It covers all 35 cases in [`../openapi/test-cases.csv`](../openapi/test-cases.csv).
- Each test's docstring cites its `TC-CUS-NNN` ID.

## Design

- **Zero setup by default.** When `API_BASE_URL` is unset, `conftest.py`
  starts the [local mock](../mock-api/README.md) on a random free port.
- **Schemas from the contract.** `assert_schema` validates responses against
  `components.schemas` of the OpenAPI file. The suite has no hand-copied
  schemas.
- **Isolated data.** Each test creates unique `@example.test` customers
  through the `create_customer` factory, and the factory deletes them
  afterwards. Tests do not depend on each other or on their order.
- **Safety guards.**
  - Non-local hosts are refused unless `ALLOW_REMOTE_TESTS=1`.
  - Tests marked `destructive` are skipped on non-local hosts unless
    `ALLOW_DESTRUCTIVE_TESTS=1`.
  - Tokens come from environment variables and are never printed:
    assertion messages show only the method, URL, status and body.
- **No sleeps.** Every request has an explicit timeout
  (`API_TIMEOUT_SECONDS`, default 5).

## Run

```bash
cd examples/pytest
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                                   # all tests against the embedded mock
pytest -m smoke                          # smoke subset
pytest -m "not destructive"              # exclude deletes
pytest --junitxml=reports/junit.xml      # JUnit report for CI
```

## Run against another environment (only if you are authorized)

```bash
export API_BASE_URL=https://staging.example.test
export API_USER_TOKEN=...   # from your secret manager, never committed
export API_ADMIN_TOKEN=...
export ALLOW_REMOTE_TESTS=1
pytest -m "smoke and not destructive"
```

[`.env.example`](.env.example) lists every supported variable. The suite
does not load `.env` files by itself, so export the variables in your shell
or your CI.

## Layout

| File | Purpose |
|---|---|
| `conftest.py` | Target selection, safety guards, tokens, schema assertion, data factory |
| `api_helpers.py` | `ApiClient` (base URL, timeout, bearer auth) and `describe()` for assertion messages |
| `tests/test_health_and_auth.py` | TC-CUS-001, 016–018 |
| `tests/test_create_customer.py` | TC-CUS-002–015, 033 |
| `tests/test_read_customers.py` | TC-CUS-019–023 |
| `tests/test_update_customer.py` | TC-CUS-024–029, 034, 035 |
| `tests/test_delete_customer.py` | TC-CUS-030–032 |

## CI

The repository workflow (`.github/workflows/ci.yml`) runs this suite on
every push.

The minimal job for your own repository is:

```yaml
- uses: actions/setup-python@v7
  with: { python-version: "3.12" }
- run: pip install -r examples/pytest/requirements.txt
- run: pytest examples/pytest --junitxml=reports/junit.xml
```
