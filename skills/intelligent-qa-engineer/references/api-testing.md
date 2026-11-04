# API Testing (Modes: GENERATE, NEGATIVE and AUTOMATE for REST APIs)

Goal: test catalogs for REST APIs, derived from the contract, that report
coverage per endpoint and per response.

## Reading an OpenAPI contract

For each operation (method + path), record:
- the parameters (path, query, header) with type, `required`, `enum`,
  `minimum`/`maximum`, `minLength`/`maxLength`, `pattern` and `format`;
- the request body schema: required fields, `additionalProperties`, nested
  objects;
- the documented responses: status codes, schemas and headers (for example
  `Location`, `Retry-After`, `ETag`);
- the security: global or per operation, the scheme, and any scopes or roles;
- whether the examples are consistent with the schemas. A mismatch is a
  contract finding.

Resolve each `$ref` before you design tests. If the contract is incomplete,
for example an error code is not documented, report it as a contract gap.

## Test catalog per operation

For each operation, consider these tests:

1. **Happy path**: valid minimal payload, valid full payload, and the
   defaults that get applied.
2. **Contract**: the status code matches the contract; the response matches
   the schema; the documented headers are present.
3. **Validation**: everything in [negative-testing.md](negative-testing.md)
   that applies to this operation's fields.
4. **Security**: authentication and authorization paths for each documented
   scheme and role.
5. **Side effects**: check them with a follow-up request, for example a
   `GET` after a `POST`. Check things such as uniqueness, state and
   counters.
6. **Business rules**: rules stated in descriptions or in the requirements.

## Endpoint coverage

Report a coverage table:

| Operation | Documented responses | Responses with ≥1 test | Positive | Negative | Notes |

A documented response is covered when at least one test asserts that status
code. Calculate:

- **Response coverage = covered documented responses / all documented
  responses.**
- **Operation coverage = operations with ≥1 test / all operations.**

Show the counts used in each calculation. List responses that you cannot
test, and say why. For example, a `500` with no way to inject a fault.

## Assertions that matter

- Status code **and** the error code inside the body, when the contract
  defines one.
- Schema validation: use JSON Schema taken from the contract, not
  hand-written partial checks.
- Values that come from the request: the echoed `name`, the normalized
  `email`, the applied defaults.
- Side effects: the resource exists or does not exist afterwards; nothing
  was created twice.
- No sensitive fields in responses, such as password hashes or internal IDs,
  when the contract excludes them.

## Environment safety

- The base URL and credentials come from environment variables. Default to a
  local mock.
- Add a guard that refuses non-local hosts unless the user opts in
  explicitly, for example with `ALLOW_REMOTE_TESTS=1`.
- Mark destructive tests (`DELETE`, bulk changes) with a marker or tag so
  they can be excluded.
