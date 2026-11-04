## What and why

<!-- What does this change and why is it needed? Link issues. -->

## Type

- [ ] Skill behaviour (SKILL.md / references / templates)
- [ ] Script or tooling
- [ ] Example
- [ ] Documentation
- [ ] CI

## Checklist

- [ ] `python tools/validate_skill.py skills/intelligent-qa-engineer` passes
- [ ] `python tools/scan_secrets.py` is clean
- [ ] `python -m pytest` and `python -m pytest examples/pytest` pass
- [ ] No duplicated instructions across SKILL.md and references
- [ ] Behaviour changes have a scenario in `tests/scenarios/scenarios.yaml`
- [ ] Manual evaluation (agent + version + result) described below, if behaviour changed
- [ ] CHANGELOG.md updated under `[Unreleased]`

## Validation performed

<!-- State what you actually ran and its result. Mark anything not run as NOT RUN. -->
