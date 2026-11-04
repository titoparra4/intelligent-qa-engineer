# Contributing

Thank you for helping improve Intelligent QA Engineer. Contributions of all
sizes are welcome: typo fixes, new negative-testing heuristics, framework
examples, translations and bug reports.

## Ground rules

1. **Keep the skill portable.** Inside `skills/intelligent-qa-engineer/`:
   - Use only spec frontmatter fields (`name`, `description`, `license`,
     `compatibility`, `metadata`, `allowed-tools`).
   - Use relative links, one level deep from `SKILL.md`.
   - Scripts may use only the Python standard library.
   - Never use absolute paths.
2. **Keep `SKILL.md` lean.** Detailed guidance belongs in `references/`.
   Do not duplicate an instruction across files. Link to it instead.
3. **No unverifiable claims.**
   - Do not add compatibility statements, badges, adoption numbers or
     benchmark results unless they come with evidence.
   - Update [docs/validation-report.md](docs/validation-report.md) when you
     verify something new, such as a platform install or a scenario run.
4. **No secrets.** Use clearly fake values (`example.test`, `local-*-token`)
   or placeholders (`${API_TOKEN}`).
5. **Examples must be reproducible.** Runnable examples target the local
   mock in `examples/mock-api/`. If you change the contract, update the mock,
   the catalog, the pytest suite and the Postman collection together. The
   tests check that they stay consistent.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Before you open a pull request

```bash
python tools/validate_skill.py skills/intelligent-qa-engineer
python tools/scan_secrets.py
python -m pytest                  # repository tests
python -m pytest examples/pytest  # example suite against the local mock
examples/postman/run-local.sh     # optional: needs Node.js
```

All of these run in CI.

## Changing behavior

If your change alters what the agent should do, for example a new rule or a
new mode:

1. Add or update a scenario in
   [tests/scenarios/scenarios.yaml](tests/scenarios/scenarios.yaml).
2. Describe in the PR how you evaluated it manually: the agent, its version,
   and the result.
3. Add an entry under `[Unreleased]` in [CHANGELOG.md](CHANGELOG.md).

## Commit and PR style

- Write small, focused PRs with a clear description of *why*.
- Use the [pull request template](.github/pull_request_template.md).
- Use English in code and documentation. Spanish translations of
  user-facing docs are welcome as `*.es.md` files.

## Code of conduct

Be respectful and constructive. Harassment or discrimination of any kind is
not tolerated. The maintainers may remove comments, commits or contributors
that violate this.
