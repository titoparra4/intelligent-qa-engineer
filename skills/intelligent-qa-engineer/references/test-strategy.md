# Test Strategy (Mode: STRATEGY)

Goal: a strategy that fits the context and shows its reasoning. Use the
template [../assets/templates/test-strategy.md](../assets/templates/test-strategy.md).

## Selecting test levels and types

Include a level or type only when there is a reason for it. Say why it is
included, or why it is excluded.

| Type | Include when | Usually exclude when |
|---|---|---|
| Unit | Logic or rules live in code you can reach; the team owns the code | Only a black-box contract is available |
| Integration | Components or services talk to databases, queues or third parties | A single component has no I/O |
| Functional | User-visible behavior is defined by acceptance criteria | Never fully excluded for a feature |
| API | An HTTP or gRPC contract exists or is being built | The feature is UI-only and has no API |
| Contract | Several consumers or providers evolve on their own; OpenAPI or Pact are available | There is one consumer and it ships with the provider |
| Smoke | Every deploy needs a quick go/no-go check | — (keep it small) |
| Regression | The change touches existing behavior | Brand-new, isolated code (use new tests instead) |
| End-to-end | A critical user journey crosses several systems | A lower level already gives the same confidence |
| Security | Authentication, authorization, input handling, personal data or money is involved | Static content only. Note: only authorized testing, never against live systems without approval |
| Performance | An NFR states a latency or throughput target, or a high-traffic path changed | No target and no risk signal. Propose it as an open question instead of inventing a target |

Follow the test pyramid as a guide, not a rule. Put each check at the
cheapest level that still gives confidence.

## Risk-based prioritization

Priority comes from Impact × Likelihood:

| | Likelihood H | M | L |
|---|---|---|---|
| **Impact H** | Critical | High | Medium |
| **Impact M** | High | Medium | Low |
| **Impact L** | Medium | Low | Low |

- Critical and High items need both positive and negative tests and are
  candidates for automation.
- Low items can rely on exploratory testing.

## Environments and data

- List the environments: local mock, CI, test, staging. Never treat
  production as a test environment unless the user explicitly authorizes it.
- For test data, say where it comes from (synthetic, factories, fixtures,
  masked copies), how it is reset, and how it stays isolated. Use unique
  values per test.
- Mock or stub third-party services in automated suites. Use contract tests
  to keep those mocks honest.

## Entry and exit criteria

Base the criteria on artifacts you can observe. Examples:

- **Entry**: the build is deployed to the target environment, smoke tests
  pass, test data is available, blocking questions are answered.
- **Exit**: all Critical and High tests have been executed; there are no
  open Critical or High defects (or an accepted waiver); every requirement
  maps to a test or to an accepted gap; residual risks are documented.

Do not invent numeric thresholds such as "95% pass rate". If the team has
thresholds, use theirs. Otherwise propose one and mark it as a proposal.

## Residual risk

List the risks that this strategy does not mitigate, and say why: out of
scope, no environment, no data, or an accepted risk.

## Tooling

Recommend tools that are already in the user's stack first. When you
propose a new tool, give a one-line reason and the cost of adopting it.
