# Test Strategy — <Feature / Release>

> Status: DRAFT · Author: <name> · Date: <YYYY-MM-DD> · Sources: <artifacts analyzed>

## 1. Objectives
- <What this testing must demonstrate, tied to business goals>

## 2. Scope
| In scope | Out of scope (and why) |
|---|---|
| <item> | <item — reason> |

## 3. Requirements and risks summary
| ID | Requirement / risk | Impact | Likelihood | Priority |
|---|---|---|---|---|
| REQ-1 | <...> | H | M | High |

## 4. Test levels and types
| Level / type | Included? | Justification | Owner |
|---|---|---|---|
| Unit | Yes/No | <reason> | <team> |
| Integration | | | |
| API / Contract | | | |
| Functional | | | |
| End-to-end | | | |
| Smoke | | | |
| Regression | | | |
| Security | | | |
| Performance | | | |

## 5. Test design approach
- Techniques per area (EP, BVA, decision tables, state transition, pairwise, error guessing) and why.

## 6. Environments
| Environment | Purpose | Data | Restrictions |
|---|---|---|---|
| Local mock | Fast feedback, CI | Synthetic | None |
| Staging | Integration | Masked | No destructive tests without approval |

## 7. Test data
- Sources, generation, isolation, cleanup, privacy constraints.

## 8. Dependencies and tooling
- <Services, mocks, tools (prefer the team's existing stack)>

## 9. Prioritization and schedule
- Critical/High first; automation candidates; smoke subset.

## 10. Entry criteria
- [ ] <observable condition>

## 11. Exit criteria
- [ ] All Critical/High tests executed with OBSERVED results
- [ ] No open Critical/High defects without waiver
- [ ] Every requirement mapped to tests or an accepted gap
- [ ] <team-specific thresholds — mark as PROPOSED if not agreed>

## 12. Residual risks
| Risk | Why not mitigated | Owner / acceptance |
|---|---|---|

## 13. Assumptions and open questions
- A-1: <assumption>
- Q-1: <question> — owner: <role>
