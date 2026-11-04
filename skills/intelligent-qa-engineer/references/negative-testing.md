# Negative & Edge Case Testing (Mode: NEGATIVE)

Goal: scenarios showing that the system rejects, limits or recovers
correctly. Each scenario needs an expected result taken from the contract or
the requirements. When the source does not define the behavior, raise an
open question. Do not assume a rule.

## Deriving the expected response

1. Use the status codes and error schema that the contract documents.
2. If the contract does not document them, use the requirements or the
   specification.
3. If neither defines them, write "Expected per HTTP semantics (assumption
   A-n)" and propose a value. Common defaults:
   - `400`: malformed syntax.
   - `401`: missing or invalid authentication.
   - `403`: authenticated, but not allowed.
   - `404`: resource not found.
   - `409`: state or uniqueness conflict.
   - `415`: unsupported media type.
   - `422`: semantic validation error. Some APIs use `400` for this.
   - `429`: rate limited.
   - `503` or `504`: a dependency is down, or a timeout.

   APIs differ. **Never assert a default code as fact** when the contract
   says otherwise.

## API negative catalog

Go through each category. Keep the ones that apply to the endpoint.

| Category | Scenarios |
|---|---|
| Required fields | Each required field missing (one at a time); `null`; empty string; whitespace only |
| Types | String where a number is expected; number as a string; boolean as a string; array instead of an object; nested type errors |
| Ranges and lengths | min-1 and max+1 for numbers and lengths; negative numbers; zero; very large numbers; too many decimal places |
| Formats | Invalid email, date, UUID or enum value; an enum value with different capitalization; trailing whitespace |
| Payload | Malformed JSON; empty body; wrong `Content-Type`; unknown fields (when `additionalProperties: false`); oversized payload |
| Authentication | No token; malformed header; invalid token; expired token; token for another environment |
| Authorization | Role without permission; reading or changing another tenant's or user's resource (IDOR); privilege escalation through fields such as `role` or `isAdmin` |
| Resources | ID that does not exist; malformed ID; deleted resource |
| State | Invalid state transition; acting on a closed or terminal entity; stale update (`ETag`/`If-Match`) |
| Uniqueness and duplicates | Duplicate create; uniqueness that ignores case (`A@x.com` vs `a@x.com`) |
| Idempotency | Retry with the same `Idempotency-Key` and the same body (expect a replay, no duplicate); same key with a different body |
| Concurrency | Two parallel updates; two parallel creates with the same unique value; read during write |
| Dependencies | Downstream returns 5xx, times out, or returns a malformed response. Check that errors are mapped and nothing is half-written |
| Timeouts | Slow responses; client timeout handling; retry policy |
| Rate limiting | Burst above the limit returns `429` with a `Retry-After` header. Test only when the limit is documented, and only against a non-production target |
| Pagination and query | `limit=0`, a negative limit, a limit above the maximum, offset past the end, invalid filter or sort field, injection-like strings |
| Injection safety | SQL, NoSQL or command metacharacters and script tags in string fields are stored or returned safely and never executed. Report the result; do not exploit it |
| Error contract | Every error response matches the error schema and does not leak stack traces or internal details |

## UI and functional edge cases

- **Field input**: empty values, maximum-length values, Unicode, emoji,
  text written right to left, and values pasted with whitespace.
- **Repeated actions**: double submits, the browser back button, refresh
  during submit, and multiple open tabs.
- **Session and time**: an expired session; timezones, daylight saving
  time, leap days, and the end of a month or year.
- **Settings**: different locales (decimal and date formats) and
  accessibility (keyboard only, screen reader labels).

## Safety

- Run destructive, concurrency, rate-limit and injection tests only against
  local or explicitly authorized environments.
- Use clearly fake data, such as `example.test` emails. Never use real
  personal data.
