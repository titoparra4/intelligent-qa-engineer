# Example 5 — Regression Analysis: simulated PR #42 (Customers API v1.0 → v1.1)

**Input:**
- [change-request.md](change-request.md);
- [openapi-v1.1.diff](openapi-v1.1.diff);
- the existing test inventory: [../openapi/test-cases.csv](../openapi/test-cases.csv), automated in [../pytest](../pytest) and [../postman](../postman).

**Prompt:** *"Build a regression test plan for this pull request."*
**Mode:** REGRESSION.
**Deliverable:** this plan and [regression-impact-matrix.csv](regression-impact-matrix.csv).

> Evidence: this analysis is `GENERATED` from the PR text and the contract
> diff. The source files listed in the PR (`src/customers/*`) are simulated
> and were not available, so call-graph impact comes from the PR's file list
> and descriptions. No v1.1 implementation exists to test. Every new and
> updated test is `NOT RUN`.

## 1. Summary

The PR has 5 changes.

**Breaking or behavioral changes (1):**
- **CHG-1:** the maximum `credit_limit` is relaxed.

**New rule (1):**
- **CHG-2:** BR-6 freezes credit increases for suspended customers.

**Additive changes (2):**
- **CHG-3:** a new `phone` field.
- **CHG-4:** a new error code.

Both additive changes are potentially breaking for strict clients.

**Refactor that claims no behavior change (1):**
- **CHG-5:** the shared validation helper.

**Recommended scope:**

| Suite | Size |
|---|---|
| Smoke | 6 tests |
| Targeted regression | 16 existing tests (reused or updated) + 7 new tests |
| Extended | The full 35-case catalog + TC-CUS-041 |

**Top risks:**
- old boundary tests that now assert the wrong thing;
- a hidden credit-ceiling assumption in downstream services;
- strict clients that reject the new `phone` field.

## 2. Changes

| ID | Change | Kind | Evidence |
|---|---|---|---|
| CHG-1 | `credit_limit.maximum` 50000 → 100000 in Customer, CustomerCreate and CustomerUpdate | Contract: limit relaxed (behavioral) | Contract diff |
| CHG-2 | BR-6: a suspended customer's credit cannot be increased (`409 credit_limit_frozen`) | Logic: new rule | PR text + diff (`info.description`) |
| CHG-3 | Optional `phone` (E.164) on requests and responses | Contract: additive | Contract diff |
| CHG-4 | Error code enum adds `credit_limit_frozen` | Contract: additive | Contract diff |
| CHG-5 | Refactor of `validate_fields()`, which create and update share | Refactor | PR file list. The author says "no behaviour change", which is an unverified claim |

## 3. Impact

**Confirmed** (follows directly from the diff or the files changed):
- Create and update validation (CHG-1, 3, 5): `validate_fields()` is shared.
- The update flow (CHG-2): `update_customer()` gains a new check.
- The response schema (CHG-3, 4).

**Hypothetical** (plausible, not visible in the inputs):

| Area | Why it might be affected | Risk |
|---|---|---|
| Downstream credit and billing consumers | They might enforce or assume the 50000 ceiling | High |
| Strict API clients | `Customer` has `additionalProperties: false`; v1.0 clients may reject `phone` | High |
| Customer creation with `status=suspended` | Whether creation counts as an "increase" is unclear | Medium |
| Reporting and exports | New column; larger values | Low (not in the matrix; no evidence) |

## 4. Existing tests

| Test | Action | Old → new expectation |
|---|---|---|
| TC-CUS-003 Accepts credit_limit boundaries | **Update** | {0, 1, 49999, 50000} → {0, 1, 99999, 100000}. 50000 is no longer a boundary |
| TC-CUS-004 Rejects credit_limit out of range (create) | **Update** | `50001 → 422` is now **wrong** (50001 is valid). New invalid boundary: `100001 → 422`. Keep -1 |
| TC-CUS-034 Rejects credit_limit out of range (update) | **Update** | Same as TC-CUS-004, for PATCH |
| TC-CUS-002, 019, 024 (Customer schema assertions) | **Reuse** | The pytest suite reads schemas from the contract. **The Postman collection embeds a schema copy, so regenerate it.** |
| TC-CUS-025, 026 (lifecycle) | **Reuse** | Guard BR-2 against the new check in `update_customer()` |
| TC-CUS-005–010, 027 (validation) | **Reuse** | Prove that the CHG-5 refactor is behavior-neutral |
| TC-CUS-010 (unknown fields) | **Reuse** | `phone` is now a known field. The test data (`id`, `role`, `is_admin`) is still valid |
| Others | **Reuse** (extended suite only) | Not affected by any change |

No test becomes obsolete.

## 5. New tests

| ID | Requirement | Title | Expected result | Technique |
|---|---|---|---|---|
| TC-CUS-036 | API-CREATE / CHG-3 | Accepts a valid E.164 phone on create and returns it | 201; `phone` echoed; schema valid | EP |
| TC-CUS-037 | API-CREATE / CHG-3 | Rejects invalid phones: `600123123` (no +), `+0123`, `+1234567890123456` (16 digits), `+34 600` (space), `+34abc` | 422 `validation_error` naming `phone` | EP + BVA |
| TC-CUS-038 | BR-6 | Increasing credit on a suspended customer is rejected | 409 `credit_limit_frozen`; credit unchanged | Decision table |
| TC-CUS-039 | BR-6 | Decreasing credit, or keeping it the same, on a suspended customer is allowed | Decrease → 200. Same value → **pending Q-R2** | Decision table + BVA |
| TC-CUS-040 | BR-2 + BR-6 | `PATCH {status: active, credit_limit: higher}` on a suspended customer | **Pending Q-R2:** is the rule evaluated on the old status or the new one? | Decision table |
| TC-CUS-041 | BR-6 | Create with `status=suspended` and `credit_limit=100000` | 201 if creation is not an "increase" (**pending Q-R3**) | Error guessing |
| TC-CUS-042 | API-GET / CHG-3 | A customer created without `phone` | `phone` is absent or `null`, as the contract defines (**pending Q-R5**). Schema valid | EP |

**Decision table for BR-6 (PATCH by a user):**

| Current status | Change in credit_limit | Status in the same request | Expected |
|---|---|---|---|
| suspended | increase | — | 409 `credit_limit_frozen` (TC-CUS-038) |
| suspended | decrease | — | 200 (TC-CUS-039) |
| suspended | equal | — | Q-R2 (TC-CUS-039) |
| suspended | increase | → active | Q-R2 (TC-CUS-040) |
| active | increase | — | 200 (existing TC-CUS-003 / 034 updated) |
| closed | any | — | 409 `invalid_state_transition` (existing TC-CUS-026; precedence over BR-6 to confirm) |

## 6. Suites

**Smoke (6):**
- TC-CUS-001;
- TC-CUS-002;
- TC-CUS-019;
- TC-CUS-024;
- TC-CUS-003 (updated: 100000 accepted);
- TC-CUS-038.

**Targeted regression (23):**
- **Updated:** TC-CUS-003, 004, 034.
- **Reused:**
  - schema: 002, 019, 024;
  - lifecycle: 025, 026;
  - validation: 005, 006, 007, 008, 009, 010, 027;
  - auth sanity on the changed operations: 016.
- **New:** 036, 037, 038, 039, 040, 041, 042.

The regression suite includes 040 and 041 even though their expected
results depend on open questions. Run them as exploratory checks, or mark
them `xfail`, until Q-R2 and Q-R3 are answered.

**Extended:** the full catalog (35 cases), plus a contract-compatibility
check against v1.0 clients if any are available.

## 7. Residual risks and open questions

| ID | Item | Type |
|---|---|---|
| Q-R1 | Which services consume `credit_limit`, and do they assume a maximum of 50000? | Residual risk: consumers are not visible |
| Q-R2 | For a suspended customer: is "equal" an increase? In a combined status + credit PATCH, is BR-6 checked against the old status or the new one? | Open question |
| Q-R3 | Does BR-6 apply on create (`status=suspended` with a high limit)? | Open question |
| Q-R4 | Will existing strict clients (`additionalProperties: false`) break on `phone`? Should the API be versioned? | Residual risk |
| Q-R5 | When `phone` is not set, is it omitted or `null`? | Open question (the contract does not say) |
| R-1 | The Postman collection's embedded schemas are stale until they are regenerated | Process risk |
| R-2 | CHG-5 "no behavior change" is backed only by the existing validation tests. No unit tests for `validate_fields()` exist in the inputs | Coverage gap |
