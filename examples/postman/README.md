# Example 3 — Postman / Newman automation

| File | Purpose |
|---|---|
| [`customers-api.postman_collection.json`](customers-api.postman_collection.json) | Postman Collection v2.1: 22 requests in 6 folders, covering 17 `TC-CUS` cases |
| [`local.postman_environment.json`](local.postman_environment.json) | Environment for the local mock. The tokens are fake demo values |
| [`run-local.sh`](run-local.sh) | Starts the mock, runs Newman, stops the mock, and writes a JUnit report |

## Design

- Every request has `pm.test` assertions on the status code, the error
  `code`, and the JSON schema (`pm.response.to.have.jsonSchema`).
- The `Customer` and `Error` schemas are copied from the OpenAPI contract
  into collection variables. **Regenerate them when the contract changes.**
  Example 5 flags this as a regression risk.
- Unique emails and idempotency keys are generated in pre-request scripts.
- Requests in a folder chain collection variables (`customerId`), so **run
  the collection in order.** This is a deliberate trade-off for Postman
  readability. The pytest suite keeps every test fully independent.
- A collection-level test checks that each response takes under 2000 ms.
  This only catches a hung local mock. **It is not a performance test.**

## Run with Newman (local mock)

Requirements: Python 3.11+ (for the mock), Node.js 18+, and `curl`.

```bash
examples/postman/run-local.sh            # port 8000
examples/postman/run-local.sh 8765       # custom port
```

The script runs `npx --yes newman@6`, which **downloads Newman** if it is
not installed. To pin a version or avoid the download, install it once:

```bash
npm install -g newman@6
```

To run it by hand against a mock that is already running:

```bash
python examples/mock-api/server.py --port 8000 &
npx newman run examples/postman/customers-api.postman_collection.json \
  -e examples/postman/local.postman_environment.json \
  -r cli,junit --reporter-junit-export reports/newman-junit.xml
```

## Run in the Postman app

1. Import both JSON files.
2. Select the **Customers API — local mock** environment.
3. Start the mock.
4. Run the collection with the Collection Runner.

For any other environment, create a separate Postman environment and store
the tokens as `secret` values. Never commit them.
