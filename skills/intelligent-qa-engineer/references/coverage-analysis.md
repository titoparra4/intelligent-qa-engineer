# Quality & Coverage Analysis (Mode: COVERAGE)

Goal: show what is covered and what is not, using numbers that are only
computed from real data.

## Coverage dimensions

| Dimension | Question | Data needed |
|---|---|---|
| Requirement coverage | Does every requirement have ≥1 test? | Requirements list + traceability |
| Scenario coverage | For each requirement, are there positive, negative and boundary tests? | Test cases with technique and tags |
| Business rule coverage | Is each rule, or each decision-table column, tested? | Rules list + tests |
| Contract coverage | Is each operation tested? Is each documented response asserted? | OpenAPI + tests (see [api-testing.md](api-testing.md)) |
| Risk coverage | Does each Critical or High risk have mitigating tests? | Risk list + tests |
| Automation coverage | Which share of tests is automated, or can be? | The `automation` column, or real test files |
| Execution coverage | Which tests actually ran, and with what result? | Execution results |
| Code coverage | Which lines and branches were executed? | **Only** from a coverage tool report (coverage.py, Istanbul/c8, JaCoCo) |

Never mix up requirement coverage and code coverage. Do not estimate code
coverage from test cases.

## Calculating metrics

Report a metric only when you have its numerator and denominator. Show both.

- Requirement coverage = requirements with ≥1 linked test / total
  requirements.
- Negative coverage = requirements with ≥1 negative test / requirements
  that need negative tests.
- Risk coverage = Critical and High risks with ≥1 test / Critical and High
  risks.
- Automation ratio = tests with `automation=Automate` that are implemented /
  tests with `automation=Automate`.

When the data is incomplete, say what is missing and give the counts you do
have. Do not give a percentage.

A test counts as "covering" a requirement only if its objective and its
expected result actually check that requirement. Report a link that is too
loose as **Partial**.

## Gap classification

- **Uncovered**: no linked test.
- **Partial**: only positive tests; boundaries missing; one role tested out
  of several; only some rule columns tested.
- **Untestable as written**: no observable acceptance criteria. Send it back
  to ANALYZE as an open question.
- **Blocked**: there is a test, but no environment, data or answer to run it.

## Report structure

1. A summary: the computed metrics with their counts, the top 5 gaps, and
   the risk exposure.
2. A traceability matrix using
   [../assets/templates/traceability-matrix.csv](../assets/templates/traceability-matrix.csv).
3. Gaps: one row per gap with its type, its severity (from risk) and a
   recommended test.
4. Test smells found in the existing suites:
   - duplicates;
   - assertion-free tests;
   - sleep-based waits;
   - order dependency;
   - hard-coded secrets.
5. Recommendations, ordered by risk reduction per unit of effort.

If Python is available, check the matrix with
`python scripts/validate_test_cases.py <cases.csv> --traceability <matrix.csv>`.
The path is relative to the skill's directory.
