# Behavioral scenarios

[`scenarios.yaml`](scenarios.yaml) defines 15 scenarios. They cover every
validation category in the product specification:

- activation and non-activation;
- traceability;
- negative coverage;
- automation;
- incomplete requirements;
- regression;
- reporting;
- secrets;
- the no-tools mode;
- prompt injection;
- bilingual answers;
- production safety.

## How they are used

| Layer | What runs | Automated? |
|---|---|---|
| Structure | `tests/test_scenarios.py` checks that the file is well formed, that every category is present, and that the fixtures exist | Yes (CI) |
| Behavior | A reviewer runs each prompt in a real agent with the skill installed, and grades `expect` / `must_not` | **No.** Manual |

## Manual grading procedure

1. Install the skill in the agent you are testing. See
   [`docs/installation.md`](../../docs/installation.md).
2. Start a fresh session in this repository, so that the fixture paths
   resolve.
3. Send the `prompt`, attaching or naming the `fixtures`.
4. Mark each `expect` item as met or not met, and each `must_not` item as
   violated or not violated.
5. Record the agent, its version, the date and the results in
   [`docs/validation-report.md`](../../docs/validation-report.md).

A scenario passes only when every `expect` item is met and no `must_not`
item is violated.
