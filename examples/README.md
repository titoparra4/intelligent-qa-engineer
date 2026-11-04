# Examples

Five complete demonstrations. Each one shows the prompt, the input and the
output the skill is expected to produce. All runnable examples target a
**deterministic local mock**, so no network access, credentials or external
services are needed.

| # | Example | Input | Output | Runnable |
|---|---|---|---|---|
| 1 | [User story testing](user-story/analysis.md) | [US-142 coupon story](user-story/input-user-story.md) (contains a planted prompt injection) | Analysis, risks, questions, [17 test cases](user-story/test-cases.csv), [traceability](user-story/traceability-matrix.csv) | Validator only |
| 2 | [REST API testing](openapi/test-catalog.md) | [Customers OpenAPI](openapi/customers-api.yaml) | [35-case catalog](openapi/test-cases.csv), negative scenarios, endpoint coverage, [traceability](openapi/traceability-matrix.csv) | Validator only |
| 3 | [Postman automation](postman/README.md) | Customers OpenAPI | [Collection](postman/customers-api.postman_collection.json), [environment](postman/local.postman_environment.json), Newman runner | Yes (Node.js) |
| 4 | [Python automation](pytest/README.md) | Customers OpenAPI | pytest suite, fixtures, configuration | Yes (Python) |
| 5 | [Regression analysis](regression/regression-analysis.md) | [Simulated PR](regression/change-request.md) + [contract diff](regression/openapi-v1.1.diff) | Impact analysis, [impact matrix](regression/regression-impact-matrix.csv), suites, gaps | — |

The mock API is in [mock-api/](mock-api/README.md).

## Re-validate the generated CSVs

```bash
python skills/intelligent-qa-engineer/scripts/validate_test_cases.py \
  examples/openapi/test-cases.csv --traceability examples/openapi/traceability-matrix.csv
python skills/intelligent-qa-engineer/scripts/validate_test_cases.py \
  examples/user-story/test-cases.csv --traceability examples/user-story/traceability-matrix.csv
```
