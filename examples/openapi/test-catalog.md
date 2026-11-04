# Example 2 — REST API Testing: Customers API

**Input:** [customers-api.yaml](customers-api.yaml) (OpenAPI 3.0.3).
**Prompt:** *"Create a test catalog with negative scenarios and endpoint coverage for this API."*
**Modes:** ANALYZE → GENERATE → NEGATIVE → COVERAGE.
**Deliverables:**
- [test-cases.csv](test-cases.csv): 35 cases.
- [traceability-matrix.csv](traceability-matrix.csv): 14 requirements.
- Automation in [../pytest](../pytest) (all 35 cases) and in [../postman](../postman) (a subset).

> Evidence: the catalog itself is `GENERATED`. Its execution status is
> recorded in [Execution evidence](#execution-evidence).

## 1. Summary

The contract has 6 operations and 24 documented responses. It also
documents 5 business rules (BR-1 to BR-5) and one bearer security scheme.

The highest risks are:
- authorization: anyone can delete, or there is no auth at all;
- duplicate customers: through email case variants, retries or races;
- the terminal `closed` state.

The catalog has 35 test cases:

| Priority | Count |
|---|---|
| Critical | 7 |
| High | 15 |
| Medium | 8 |
| Low | 5 |

All 24 documented responses are asserted by at least one test.

## 2. Requirements extracted

| ID | Statement | Source | Status |
|---|---|---|---|
| API-HEALTH | `GET /health` → 200 `{status: ok}`, no auth | `paths./health` | Confirmed |
| API-LIST | List with `limit` 1..100 (default 20), `offset` ≥ 0, `status` filter | `paths./customers.get` | Confirmed |
| API-CREATE | Create validates `CustomerCreate`; 201 + `Location` | `paths./customers.post` | Confirmed |
| API-GET / API-UPDATE / API-DELETE | Read, partial update (`minProperties: 1`), delete | `paths./customers/{customerId}` | Confirmed |
| API-ERR | Errors use `components.schemas.Error` | `components.responses` | Confirmed |
| SEC-AUTH | Bearer auth on all `/customers` operations | global `security` | Confirmed |
| BR-1 … BR-5 | Unique email (case-insensitive); lifecycle; credit limit 0..50000; admin-only delete; idempotent create | `info.description` | Confirmed |
| NFR-RATE | Rate limiting | — | **Open question Q-1** |

## 3. Risks

| ID | Risk | Impact | Likelihood | Priority | Mitigating tests |
|---|---|---|---|---|---|
| RISK-1 | Missing or incorrect authorization on an operation (for example, a user can delete) | H | H | Critical | TC-CUS-016–018, 031 |
| RISK-2 | Duplicate customers from email case variants, client retries or races | H | H | Critical | TC-CUS-013, 014, 015, 028, 033 |
| RISK-3 | Credit limit accepted outside 0..50000 (financial exposure) | H | M | High | TC-CUS-003–005, 034 |
| RISK-4 | A closed customer is modified or reactivated | H | M | High | TC-CUS-025, 026 |
| RISK-5 | Pagination returns inconsistent pages | L | M | Low | TC-CUS-021, 023 |

## 4. Test design choices

| Technique | Applied to | Reason |
|---|---|---|
| BVA | `credit_limit`, `name` length, `limit` | The contract has explicit numeric and length limits |
| EP | email formats, status enum, types, tokens | The input domains split into classes, each with the same expected behavior |
| State transition | BR-2 lifecycle | Every valid transition, and every exit from the terminal state |
| Decision table | BR-1 on update (other customer's email vs own email re-cased) | The outcome depends on whose email it is and on the case |
| Error guessing | malformed JSON, mass-assignment fields (`role`, `is_admin`), concurrency | Common defect classes that the schema alone does not show |
| Risk-based | auth on every operation, idempotency | Critical risks get negative tests on every operation |

**Not selected:**
- **Performance.** The contract has no NFR → Q-1.
- **Pairwise.** The operations have at most 3 independent parameters, so the
  full combination set is already small.

## 5. Negative scenarios (summary)

| Category | Scenarios | Cases |
|---|---|---|
| Required fields | `name` and `email` missing, one at a time | 006 |
| Types | `credit_limit` as `"100"`, `10.5`, `true`, `null`; `name`/`email` as numbers | 005, 007, 008 |
| Ranges and lengths | `credit_limit` -1/50001 (create and update); `name` 101 chars; `limit` 0/101; `offset` -1 | 004, 007, 023, 034 |
| Formats and enums | 6 invalid emails; status `closed`/`ACTIVE`/`deleted` on create | 008, 009 |
| Payload | Truncated JSON, empty body, `[]`, string; `text/plain`; form-encoded | 011, 012, 035 |
| Mass assignment | Unknown `id`, `role`, `is_admin` | 010 |
| Authentication | No token on all 5 protected operations; invalid token; wrong scheme; expired token | 016, 017, 018 |
| Authorization | User role calls DELETE | 031 |
| Resources | Unknown and malformed ids on GET, PATCH and DELETE | 020, 029, 032 |
| State | Every change to a `closed` customer | 026 |
| Duplicates | Email upper-cased on create and on update | 013, 028 |
| Idempotency | Replay with the same key; key reuse with a different body | 014, 015 |
| Concurrency | 8 parallel creates with the same email | 033 |

These categories were reviewed but **not tested**, because the contract does
not define the expected behavior:
- rate limiting (Q-1);
- payload size limit (Q-2);
- lost updates without `ETag`/`If-Match` (Q-3);
- dependency failures (the API has no dependencies documented).

## 6. Endpoint coverage

A documented response counts as covered when at least one test asserts that
status code.

| Operation | Documented responses | Covered | Positive | Negative | Cases |
|---|---|---|---|---|---|
| `GET /health` | 200 | 1/1 | 1 | 0 | 001 |
| `GET /customers` | 200, 401, 422 | 3/3 | 3 | 2 | 016, 021–023 |
| `POST /customers` | 201, 400, 401, 409, 415, 422 | 6/6 | 3 | 12 | 002–016, 033 |
| `GET /customers/{id}` | 200, 401, 404 | 3/3 | 1 | 2 | 016, 019, 020 |
| `PATCH /customers/{id}` | 200, 400, 401, 404, 409, 415, 422 | 7/7 | 3 | 6 | 016, 024–029, 034, 035 |
| `DELETE /customers/{id}` | 204, 401, 403, 404 | 4/4 | 1 | 3 | 016, 030–032 |

- **Response coverage:** 24 covered / 24 documented responses.
- **Operation coverage:** 6 / 6 operations.

Some cases count under more than one operation. TC-CUS-016 covers the `401`
of all five protected operations.

**Requirement coverage** (from the traceability matrix, as computed by
`validate_test_cases.py`): 13 of 14 requirements have at least one test.
- `NFR-RATE` is *Untestable* until Q-1 is answered.
- `SEC-AUTH` and `API-ERR` are *Partial*.

This is requirement and contract coverage, not code coverage.

## 7. Contract gaps and open questions

| ID | Question | Why it matters | Owner |
|---|---|---|---|
| Q-1 | Is there rate limiting? What are the limits, and does it return `429` + `Retry-After`? | Abuse resistance; client retry behavior | API owner |
| Q-2 | What is the maximum request size? Should `413`, `405` and `500` be documented? | Undocumented responses cannot be checked against the contract | API owner |
| Q-3 | Should `PATCH` support optimistic locking (`ETag`/`If-Match`)? | Concurrent updates are currently last-write-wins | Architect |
| Q-4 | How are roles defined in tokens? Are tokens bound to an environment? | Without this, privilege and cross-environment tests cannot be designed | Security |
| Q-5 | Is the email stored as sent, or normalized to lowercase? | Affects search and the meaning of "duplicate" | Product |
| Q-6 | How long are Idempotency-Keys kept, and are they scoped per user? | One user could replay another user's response | Architect |
| Q-7 | Can a suspended customer's `credit_limit` change? | Business rule gap (used in [Example 5](../regression/regression-analysis.md)) | Product |

## Execution evidence

Results are `SIMULATED`: the tests ran against the local mock
[../mock-api/server.py](../mock-api/server.py), which implements this
contract. This shows that the tests work and agree with the contract. It
does not show that any real implementation is correct. See
[../../docs/validation-report.md](../../docs/validation-report.md) for the
recorded runs.
