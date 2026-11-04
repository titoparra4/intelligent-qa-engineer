# Validation report — v0.1.0

**Date:** 2026-11-04
**Environment:** macOS (Darwin 27.2), Python 3.9.6, Node.js 24.15.0, Newman 6.2.3, Claude Code CLI (`claude plugin validate`)
**Commit:** v0.1.0 (merged to `main` as `970b944` via PR #1)

This report keeps four kinds of evidence apart, as the product specification
requires:

1. **Static validation**: structure and consistency checks. Nothing is
   executed against a service.
2. **Executed automated tests**: real runs with output that was observed.
3. **Manual behavioral evaluation**: an agent using the skill, graded by a
   human.
4. **Platform compatibility**: an install plus a working invocation on each
   platform.

All results below were actually observed in the environment above, unless
they are marked **PENDING**.

## 1. Static validation

| Check | Tool | Result |
|---|---|---|
| `SKILL.md` frontmatter: name rules, name = directory, description ≤ 1024 (873 chars), portable fields only, metadata values are strings | `tools/validate_skill.py` | **PASS** |
| `SKILL.md` size: 181 lines (limit 500); body about 1,920 tokens (recommended under 5,000) | `tools/validate_skill.py` | **PASS** |
| All relative links inside the skill resolve and stay inside it; every `references/*.md` file is linked from `SKILL.md` | `tools/validate_skill.py` | **PASS** |
| No absolute paths in the skill; the bundled script compiles | `tools/validate_skill.py` | **PASS** |
| All Markdown links in the repository resolve | `tests/test_repo_hygiene.py` | **PASS** |
| No secrets in the repository: 0 high-confidence and 0 low-confidence findings | `tools/scan_secrets.py` | **PASS** |
| The example CSV deliverables are valid in `--strict` mode: user story with 17 cases and 9 requirements; OpenAPI with 35 cases and 14 requirements | `validate_test_cases.py` | **PASS** (0 errors, 0 warnings) |
| The Postman collection follows v2.1; every request has tests; the TC IDs exist in the catalog; the embedded schemas equal the schemas taken from the contract; the scripts are valid JavaScript (`node --check`) | `tests/test_examples.py` | **PASS** |
| The pytest suite implements exactly the 35 catalog IDs; it has no `time.sleep`; every request has a timeout | `tests/test_examples.py` | **PASS** |
| The regression impact matrix uses valid enums, refers to existing or newly defined tests, and contains both confirmed and hypothetical impact | `tests/test_examples.py` | **PASS** |
| The Claude Code plugin and marketplace manifests are valid | `claude plugin validate .` | **PASS** with 1 warning (no plugin icon) |
| Reference validator `skills-ref validate` | agentskills `skills-ref` | **PENDING.** Installing it from the network was not permitted in the build environment |

## 2. Executed automated tests

| Suite | Command | Result | Evidence label |
|---|---|---|---|
| Repository tests: skill structure, validator unit tests, examples, hygiene, scenario structure | `python -m pytest` | **114 passed, 0 failed** | OBSERVED |
| pytest example against the local mock (all 35 cases, 80 parametrized tests) | `python -m pytest examples/pytest` | **80 passed, 0 failed** | SIMULATED (mock) |
| Marker selection | `-m smoke` / `-m "not destructive"` | 3 selected and passed / 79 selected and passed | SIMULATED |
| Postman collection through Newman against the local mock | `examples/postman/run-local.sh` | **22 requests, 82 assertions, 0 failed** | SIMULATED (mock) |
| Mutation check: does the suite catch real defects? | In-memory mutants of the mock | See below | SIMULATED |

**Mutation check.** Three defects were injected into an in-memory copy of
the mock. The source files were not changed. The pytest example ran against
each mutant:

| Mutant | Failures detected |
|---|---|
| `credit_limit` maximum off by one (accepts 50001) | 3 tests failed: TC-CUS-004 and TC-CUS-034. TC-CUS-021 also failed, because the record that the negative test unexpectedly created broke the `CustomerList` schema |
| Email uniqueness becomes case-sensitive (BR-1) | 2 tests failed (TC-CUS-013, TC-CUS-028) |
| Admin check removed from DELETE (BR-4) | 1 test failed (TC-CUS-031) |

All 3 mutants were caught.

**GitHub Actions (PR #1):**
- **Newman job** and **Python 3.12 job:** passed on the first run.
- **Python 3.9 job:** could not run, because `actions/setup-python` has no
  3.9 build for the current `ubuntu-latest` image (Ubuntu 26.04). The matrix
  now uses 3.10 and 3.12. Python 3.9 compatibility rests on the local runs
  above (3.9.6).
- **Second run (commit `232a3d4`):** all 4 jobs passed. These were
  *Validate skill and tests* on Python 3.10 and 3.12, *Postman collection
  via Newman*, and *Package skill*. The PR was then merged into `main` as
  `970b944`.

**What the examples' evidence means.** These are `SIMULATED` results: they
ran against a mock written from the same contract. They show that the
generated tests run, use the contract correctly and catch the injected
defects. They show nothing about any real Customers API.

## 3. Manual behavioral evaluation

The 15 scenarios in [tests/scenarios/scenarios.yaml](../tests/scenarios/scenarios.yaml)
cover the 12 behavior categories that the specification requires:

- activation and non-activation;
- traceability;
- negative coverage;
- automation;
- incomplete requirements;
- regression;
- reporting;
- secrets;
- no tools;
- prompt injection;
- bilingual answers;
- production safety.

| Scenario | Claude Code | Codex | ChatGPT |
|---|---|---|---|
| S01–S15 | **PENDING** | **PENDING** | **PENDING** |

The only automated check here is the structure of the scenario file. That
check **PASSES**.

The examples were written by following the skill's own procedure. Example 1
shows the intended response to the planted injection. That shows design
intent only. No agent session has been graded yet.

## 4. Platform compatibility

| Platform | Install verified | Invocation verified | Notes |
|---|---|---|---|
| Claude Code | **PENDING** | **PENDING** | The layout follows the documented `~/.claude/skills` and `.claude/skills` locations. The plugin manifests pass `claude plugin validate` |
| OpenAI Codex | **PENDING** | **PENDING** | The layout follows the documented `.agents/skills` locations |
| ChatGPT | **PENDING** | **PENDING** | Custom skill upload depends on plan and workspace. Not confirmed |
| Other Agent Skills agents | **PENDING** | **PENDING** | Conforms to the specification (section 1) |

## Known limitations

- Behavior and platform checks need live agents (sections 3 and 4).
- Playwright and Jest/Vitest are covered by guidance only. There is no
  runnable example yet.
- The validator checks structure and consistency, not whether the test
  design is good.
- The CSV columns are fixed in English.
- A negative test that unexpectedly succeeds (gets a 201) does not clean up
  the record it created. The mutation run shows this: the leaked record
  caused a second failure in TC-CUS-021. With the per-session mock this is
  harmless. Against a persistent environment it would leave data behind.
  The fix is on the roadmap.
- `jsonschema`'s `date-time` format check needs an optional extra package
  (`rfc3339-validator`). Without it, `date-time` values in the pytest
  example are not format-checked.

## How to reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python tools/validate_skill.py skills/intelligent-qa-engineer
python tools/scan_secrets.py
python -m pytest
python -m pytest examples/pytest
examples/postman/run-local.sh
claude plugin validate .     # requires Claude Code
```
