# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- CI: GitHub Actions bumped to the Node 24 majors (`checkout`, `setup-python`,
  `setup-node`, `upload-artifact` @v7); Newman runs on Node 24.
- CI: runner pinned to `ubuntu-24.04` instead of `ubuntu-latest`, so the
  Python 3.10 job does not break when the image moves on.

### Added

- Dependabot: security updates enabled and `.github/dependabot.yml` for weekly
  GitHub Actions and pip updates.

## [0.1.0] — 2026-11-04

### Added

- **The skill: `skills/intelligent-qa-engineer`.**
  - `SKILL.md` with nine modes (ANALYZE, STRATEGY, GENERATE, NEGATIVE,
    AUTOMATE, REGRESSION, COVERAGE, REPORT, FULL-QA) and an 8-step workflow.
  - Core rules (no invented requirements, evidence labels, execution
    statuses) and mandatory safety rules.
  - Nine reference modules, one per mode, loaded on demand.
  - Templates: test cases, traceability matrix, regression impact matrix,
    test strategy and QA report.
  - `scripts/validate_test_cases.py`: a validator for test-case CSVs and
    traceability matrices that uses only the standard library.
- **Five worked examples:**
  - user story;
  - OpenAPI catalog;
  - Postman/Newman;
  - pytest;
  - regression analysis.

  They come with a deterministic local mock of the Customers API.
- **Repository tooling and checks:**
  - `tools/validate_skill.py` (spec and portability checks);
  - `tools/scan_secrets.py`;
  - repository tests;
  - 15 behavioral scenarios for manual evaluation.
- **Claude Code plugin and marketplace manifests.**
- **Project documentation:**
  - installation guide for Claude Code, Codex, ChatGPT (unverified) and
    other agents;
  - validation report;
  - security policy;
  - contribution guide.
- **GitHub Actions CI** on Python 3.10 and 3.12, with Newman, plus a
  packaged skill zip as an artifact.
