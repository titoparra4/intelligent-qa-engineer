# Test Automation (Mode: AUTOMATE)

Goal: runnable, maintainable automation with configuration, dependencies and
run commands. Do not write pseudocode.

## Choosing a framework

1. Use the framework the repository already uses. Check `package.json`,
   `requirements*.txt`, `pyproject.toml`, existing test folders and CI
   files.
2. Otherwise, choose by context:

| Framework | Good fit |
|---|---|
| Postman / Newman | Teams that share collections; manual and automated use together; CI through Newman |
| Python + pytest + requests + jsonschema | Python teams; data-driven tests; strong fixtures |
| Playwright API testing (`@playwright/test` `request` fixture) | JS/TS teams that already use Playwright for UI, or that want one runner for UI and API |
| Jest or Vitest + fetch or supertest | JS/TS services tested in the same repository (supertest for in-process apps) |

State which framework you chose and why, in one line.

## Required structure

Every automation deliverable includes all of the following:

- **Dependencies** with bounded versions (`requirements.txt`,
  `package.json`). Do not add libraries the tests do not use.
- **Configuration**:
  - base URL, tokens and timeouts come from environment variables;
  - a committed `.env.example` or environment file contains placeholders or
    local mock values only;
  - real `.env` files are git-ignored.
- **Fixtures and helpers**:
  - an authenticated client;
  - data factories that create unique data (for example
    `uuid4().hex`-based emails on `example.test`);
  - cleanup when the target keeps data.
- **Tests**:
  - grouped by resource or feature;
  - named after the behavior they check;
  - linked to test case IDs in the docstring or test name, for example
    `TC-CUS-012`.
- **Markers and tags**: `smoke`, `negative`, `contract`, `destructive`.
- **Schema validation** using schemas taken from the contract.
- **Reporting**:
  - pytest: `--junitxml=reports/junit.xml`;
  - Newman: `-r cli,junit --reporter-junit-export reports/newman.xml`;
  - Playwright: the `junit` or `html` reporter.
- **README**: prerequisites, install, configure, run all tests, run a single
  marker, and the CI snippet.
- **CI job**: a minimal GitHub Actions, GitLab CI or similar job that runs
  against a local mock or an ephemeral environment.

## Quality rules

- No fixed sleeps. Use polling with a timeout when waiting for something
  asynchronous.
- Every request has an explicit timeout.
- Tests run in any order and do not depend on each other. Data is unique
  for each test. Shared setup goes in fixtures, not in earlier tests. The
  Postman exception: requests inside one folder may chain variables. Say so
  in the README.
- Assertions check meaning (see [api-testing.md](api-testing.md)). The
  assertion message shows the response body when a check fails.
- Tests must give the same result on every run. Make clocks, random seeds
  and external services fixed or mocked.
- Secrets are never printed. Redact `Authorization` headers in logs.
- Mark a known product bug as an expected failure (for example
  `pytest.mark.xfail`), with the defect ID. Do not delete the test.

## Verifying generated code

In this order, as far as the environment allows:

1. **Syntax.** Run `python -m py_compile` on each file, `node --check` on
   each JavaScript file, or parse the Postman JSON.
2. **Collection.** Run `pytest --collect-only -q` or
   `npx playwright test --list`.
3. **Execution.** Run only against a local mock, or against a target the
   user authorized. Report the real counts of `PASS`, `FAIL` and `SKIP`.

If you could not run a step, say that it is `NOT RUN` and give the exact
command for the user to run.
