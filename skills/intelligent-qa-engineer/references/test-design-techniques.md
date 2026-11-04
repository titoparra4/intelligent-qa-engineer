# Test Design Techniques (Mode: GENERATE)

Goal: the smallest set of test cases that covers the relevant equivalence
classes, boundaries, rule combinations and states.

## Test case format

Use the columns of [../assets/templates/test-cases.csv](../assets/templates/test-cases.csv):

| Column | Rule |
|---|---|
| `test_case_id` | `TC-<AREA>-<NNN>`, unique (for example `TC-CPN-001`) |
| `requirement_id` | One or more existing requirement IDs, separated by `;` |
| `title` | Behavior under test + condition ("Rejects coupon expired yesterday") |
| `objective` | One verifiable sentence |
| `priority` | `Critical`, `High`, `Medium` or `Low` (from risk) |
| `preconditions` | State that must exist before the test runs |
| `test_data` | Concrete values, or a reference to a data set. Never real personal data or secrets |
| `steps` | Numbered steps, separated by ` | ` inside the CSV cell |
| `expected_result` | Observable, specific outcome. Avoid wording like "works correctly" |
| `test_type` | `Functional`, `API`, `Integration`, `Unit`, `E2E`, `Regression`, `Smoke`, `Security`, `Performance`, `Contract`, `Usability` or `Accessibility` |
| `technique` | `EP`, `BVA`, `Decision table`, `State transition`, `Pairwise`, `Error guessing`, `Risk-based`, `Use case` or `Exploratory` |
| `automation` | `Automate` (stable, repeatable, high value), `Candidate` (needs a test hook or data), `Manual` (judgment or visual) |
| `tags` | Free tags separated by `;`, for example `smoke;negative;auth` |

## Techniques and when to use them

**Equivalence partitioning (EP).** Use it for any input with a domain. Pick
one representative per valid class and one per invalid class. Test invalid
classes one at a time so that a failure points to its cause.

**Boundary value analysis (BVA).** Use it for numeric ranges, lengths, dates
and counts. For a range [min, max], test min-1, min, max and max+1. Add
min+1 and max-1 only when the implementation is likely to have off-by-one
logic. When it is unclear whether a boundary is inclusive, create an open
question and test both sides.

**Decision tables.** Use them when the outcome depends on a combination of
conditions. Build the full table, merge columns that lead to the same
action, and turn each remaining column into one test case. Mark
combinations that cannot happen.

**State transition.** Use it for lifecycles such as orders, accounts or
subscriptions.
- List the states and the allowed transitions.
- Test every valid transition at least once (0-switch coverage).
- Test the important invalid transitions, especially out of terminal states.

**Pairwise.** Use it when there are three or more independent parameters
with several values each. Generate a pairwise set; name the tool used, or
show the table. Add specific combinations for high-risk pairs.

**Error guessing.** Use experience-based tests for null or empty values,
whitespace, Unicode and emoji, very long values, duplicate submits, double
clicks, timezones, leap days, retries and stale data.

**Risk-based.** Spend most of the effort on Critical and High risk areas.
Each Critical risk needs at least one negative test.

**Use case.** Use it for end-to-end flows: the main path plus each
alternative or exception path.

## Avoiding redundancy

- Each test must add a new class, boundary, rule column, transition or risk.
  Drop tests that only repeat another value from an already covered class.
- Merge tests that differ only in data into one data-driven test. List the
  data set in `test_data`.
- Do not test the framework or the language itself. For example, "returns
  JSON" is a contract check, so make it an assertion inside other tests.

## Self-check before you deliver

- Every requirement has a test, or it is listed as a gap.
- Every Critical or High requirement has at least one negative test.
- No two tests share an ID.
- Each expected result can be checked by someone who did not write the test.
