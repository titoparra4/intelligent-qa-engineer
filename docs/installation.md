# Installation guide

The skill is the folder
[`skills/intelligent-qa-engineer/`](../skills/intelligent-qa-engineer/SKILL.md).
Every installation method below puts that folder, with its name unchanged,
where your agent looks for skills.

The folder name must stay `intelligent-qa-engineer`. The Agent Skills
specification requires the `name` field to match the directory name.

> **How the information here was verified.** The skill locations below come
> from each vendor's documentation, as read on 2026-11-04:
> - Claude Code: <https://code.claude.com/docs/en/skills>
> - Codex: <https://developers.openai.com/codex/skills> (it redirects to <https://learn.chatgpt.com/docs/build-skills>)
> - the Agent Skills specification: <https://agentskills.io/specification>
>
> Product behavior changes over time, so check the linked page if a step
> does not work. The [validation report](validation-report.md) records
> which installs were actually tested.

Get the files once:

```bash
git clone https://github.com/titoparra4/intelligent-qa-engineer.git
cd intelligent-qa-engineer
```

---

## Claude Code

Claude Code discovers skills in these places:
- `~/.claude/skills/<name>/SKILL.md` (personal, all projects);
- `.claude/skills/<name>/SKILL.md` (project; commit it to share it with
  your team);
- installed plugins.

### Option A: personal skill

```bash
mkdir -p ~/.claude/skills
cp -R skills/intelligent-qa-engineer ~/.claude/skills/
```

### Option B: project skill (shared through git)

```bash
cd /path/to/your-project
mkdir -p .claude/skills
cp -R /path/to/intelligent-qa-engineer/skills/intelligent-qa-engineer .claude/skills/
git add .claude/skills/intelligent-qa-engineer
```

### Option C: plugin from this repository's marketplace

This repository contains `.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json`. Both pass `claude plugin validate .`.

Inside Claude Code, run:

```text
/plugin marketplace add titoparra4/intelligent-qa-engineer
/plugin install intelligent-qa-engineer@intelligent-qa-engineer
```

Plugin skills are namespaced, so after a plugin install the skill is invoked
as `/intelligent-qa-engineer:intelligent-qa-engineer`.

### Use it

Claude activates the skill automatically when a request matches its
description. You can also invoke it explicitly:

```text
Analyze docs/stories/US-142.md and generate test cases with traceability.
/intelligent-qa-engineer REGRESSION for the current git diff
```

Claude Code picks up skill file changes during a session. If the skill does
not appear, start a new session and check the folder path.

**Update:** copy the folder again, or run `/plugin marketplace update`.

**Uninstall:** delete the folder, or run
`/plugin uninstall intelligent-qa-engineer@intelligent-qa-engineer`.

---

## OpenAI Codex (CLI and IDE extension)

According to the Codex documentation, Codex scans:
- `.agents/skills/` in the current directory and in each parent directory
  up to the repository root;
- `$HOME/.agents/skills/` for user skills;
- `/etc/codex/skills/` for admin skills.

### User skill

```bash
mkdir -p ~/.agents/skills
cp -R skills/intelligent-qa-engineer ~/.agents/skills/
```

### Repository skill

```bash
cd /path/to/your-repo
mkdir -p .agents/skills
cp -R /path/to/intelligent-qa-engineer/skills/intelligent-qa-engineer .agents/skills/
```

### Use it

Codex can select the skill on its own from the description. To invoke it
explicitly, type `$` followed by the skill name, or browse with `/skills`:

```text
$intelligent-qa-engineer generate pytest automation for openapi.yaml
```

If a newly added skill does not appear, restart Codex.

Codex also has a built-in `$skill-installer`. Its documentation describes
installing curated skills, and says it can install skills from other
repositories, but it does not document the URL format. Installing this
repository that way has **not been verified**, so use the copy method above.

---

## ChatGPT

> **Status: not verified by the maintainers.**

OpenAI documents standalone skills in the **ChatGPT desktop app**, where you
open *Skills* in the sidebar and select a skill with `@`. It also documents
skills bundled inside plugins in ChatGPT web, desktop and mobile.

Whether you can **add your own** skill depends on your product, plan and
workspace settings. In a managed workspace, an admin may control it. This
guide does not assume that every user can install a skill from a GitHub URL.

### If your ChatGPT offers custom skills

1. Package the skill folder as a zip, keeping the folder as the zip's
   top-level entry:
   ```bash
   cd skills && zip -r ../intelligent-qa-engineer.zip intelligent-qa-engineer && cd ..
   ```
   CI also builds this zip as a downloadable artifact.
2. In ChatGPT, open **Skills** and use the option to create or upload a
   skill. Select the zip, or the folder if your version accepts folders.
3. Start a chat and select the skill with `@intelligent-qa-engineer`, or
   just describe the task.

The exact menu names vary between versions. Follow OpenAI's current help
article on skills.

### Fallback: when custom skills are not available

This is an **adaptation**, not a skill install. In this mode, progressive
disclosure and script execution may not be available.

1. Create a **Project**, or a custom GPT if your plan allows it.
2. Paste the body of `SKILL.md`, everything after the `---` frontmatter,
   into the project or GPT **instructions**.
3. Upload these files as **project files** or **knowledge**:
   - the files in `references/`;
   - the files in `assets/templates/`.
4. Ask the same natural-language requests. The skill's "analysis mode"
   rules apply: deliverables come inline, and results are `NOT RUN` unless
   you run them.

If your workspace has Code Interpreter or data analysis, also upload
`scripts/validate_test_cases.py` and ask ChatGPT to run it on the generated
CSVs.

---

## Other Agent Skills–compatible agents

### Option A: `skills` CLI (skills.sh)

The open-source [`skills` CLI](https://github.com/vercel-labs/skills) installs
skills straight from a GitHub repository, without cloning it first:

```bash
npx skills add titoparra4/intelligent-qa-engineer
```

Update later with `npx skills update`. By default the CLI sends anonymous
telemetry (skill name, skill files, timestamp) that ranks skills on
<https://skills.sh>. Set `DISABLE_TELEMETRY=1` to opt out.

> This path is documented at <https://skills.sh/docs> (read on 2026-11-04)
> but is **not yet verified** in the [validation report](validation-report.md).

### Option B: manual copy

Copy `skills/intelligent-qa-engineer/` into the skills directory your agent
documents. Keep the folder name and the structure unchanged.

The skill follows the specification in these ways:
- it uses only the portable frontmatter fields (`name`, `description`,
  `license`, `compatibility`, `metadata`);
- its links are relative, one level deep;
- its scripts use only the Python standard library.

Before relying on any agent, check it with
[`tests/scenarios`](../tests/scenarios/README.md).

---

## Verify the package

```bash
pip install -r requirements-dev.txt
python tools/validate_skill.py skills/intelligent-qa-engineer
```

The optional reference validator, `skills-ref validate
skills/intelligent-qa-engineer`, comes from the
[agentskills](https://github.com/agentskills/agentskills) project. It is
not bundled with this repository.
