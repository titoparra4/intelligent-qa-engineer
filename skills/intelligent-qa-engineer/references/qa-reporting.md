# QA Reporting (Mode: REPORT)

Goal: a report that decision makers can trust. It keeps what was executed
separate from what was only designed. Use
[../assets/templates/qa-report.md](../assets/templates/qa-report.md).

## Status vocabulary

| Status | Meaning |
|---|---|
| `PASS` | Executed, and the observed result matched the expected result |
| `FAIL` | Executed, and the observed result did not match. Link a defect |
| `BLOCKED` | Could not execute because of an environment, data, dependency or open question. State the blocker |
| `NOT RUN` | Not executed: not yet run, out of time, deselected, or only generated |

Every result also carries an evidence label: `OBSERVED` (real execution
output), `SIMULATED` (run against a mock), or `GENERATED` / `EXPECTED`
(nothing ran).

## Rules

- Take execution numbers only from real results: JUnit XML, Newman output,
  pytest output, or results the user provides. Cite the source file or the
  run.
- Report generated tests in a **separate inventory section**, never inside
  the execution results.
- Defects need an ID, a severity (Critical/High/Medium/Low), steps to
  reproduce, the expected and actual results, and the environment.
- Severity describes the impact on users or the business. It is not the same
  as priority.

## Release readiness assessment

Give one of these recommendations: **Ready**, **Ready with risks**, **Not
ready** or **Insufficient evidence**.

- **Ready**: needs executed evidence (`OBSERVED`) for all Critical and High
  scope, no open Critical or High defects without a waiver, and the exit
  criteria met.
- **Insufficient evidence**: give this whenever the only evidence is
  generated tests, or executions against mocks for behavior that depends on
  real integrations.
- Always list the reasons, the residual risks and the conditions that would
  change the recommendation.

The assessment is advice. The release decision belongs to the team.

## Report sections

1. **Executive summary.** 3 to 6 bullets: the recommendation, key numbers
   with their sources, the top risks.
2. **Scope.** What is in scope, what is out, and the build, version and
   environment.
3. **Test inventory.** The generated and existing tests by type, priority and
   automation status.
4. **Execution results.** PASS, FAIL, BLOCKED and NOT RUN counts, by suite,
   with the evidence source.
5. **Defects.** Open and closed, by severity.
6. **Coverage gaps.** From COVERAGE.
7. **Risks.** Residual risks, with impact.
8. **Blockers.** What is blocking and who owns it.
9. **Recommendations.** Concrete next actions.
10. **Release readiness assessment.**
11. **Appendix.** The commands run, the tool versions, and links to the raw
    reports.
