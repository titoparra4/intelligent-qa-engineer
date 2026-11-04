#!/usr/bin/env python3
"""Validate an Agent Skill directory against the Agent Skills specification
(https://agentskills.io/specification) plus this repository's portability rules.

    python tools/validate_skill.py skills/intelligent-qa-engineer
    python tools/validate_skill.py skills/intelligent-qa-engineer --json

Checks:
  * SKILL.md exists and starts with YAML frontmatter
  * name: 1-64 chars, [a-z0-9-], no leading/trailing/consecutive hyphens,
    equals the parent directory name
  * description: 1-1024 chars
  * only portable top-level fields (name, description, license,
    compatibility, metadata, allowed-tools); compatibility <= 500 chars;
    metadata is a string->string map
  * SKILL.md under 500 lines; body under ~5000 tokens (estimated)
  * every relative Markdown link inside the skill resolves and stays inside it
  * every file in references/ is linked from SKILL.md
  * no absolute local paths; Python scripts compile

Exit codes: 0 valid, 1 invalid, 2 usage error. Requires PyYAML.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only without dev deps
    print("error: PyYAML is required (pip install -r requirements-dev.txt)", file=sys.stderr)
    sys.exit(2)

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
MAX_LINES = 500
MAX_BODY_TOKENS = 5000
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
ABSOLUTE_PATH_RE = re.compile(r"(?:/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/|[A-Za-z]:\\\\Users\\\\)")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "#")


def split_frontmatter(text: str) -> Tuple[Optional[str], str]:
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None, text
    lines = text.splitlines(keepends=True)
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "".join(lines[1:index]), "".join(lines[index + 1:])
    return None, text


def iter_links(markdown: str) -> Iterable[str]:
    in_fence = False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK_RE.finditer(re.sub(r"`[^`]*`", "", line)):
            yield match.group(1)


def check_markdown_links(files: Iterable[Path], confine_to: Optional[Path] = None) -> List[str]:
    """Return errors for relative links that do not resolve (or escape confine_to)."""
    errors: List[str] = []
    for md in files:
        for target in iter_links(md.read_text(encoding="utf-8")):
            if target.startswith(EXTERNAL_PREFIXES):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            resolved = (md.parent / path_part).resolve()
            if not resolved.exists():
                errors.append(f"{md}: broken link '{target}'")
            elif confine_to is not None and confine_to.resolve() not in (resolved, *resolved.parents):
                errors.append(f"{md}: link '{target}' points outside the skill directory")
    return errors


def validate_frontmatter(meta: Dict, skill_dir: Path, errors: List[str], warnings: List[str]) -> None:
    unknown = sorted(set(meta) - ALLOWED_FIELDS)
    if unknown:
        errors.append(f"frontmatter: non-portable field(s) {unknown}; allowed: {sorted(ALLOWED_FIELDS)}")
    name = meta.get("name")
    if not isinstance(name, str) or not name:
        errors.append("frontmatter: 'name' is required and must be a string")
    else:
        if len(name) > 64:
            errors.append(f"frontmatter: name is {len(name)} chars (max 64)")
        if not NAME_RE.match(name):
            errors.append("frontmatter: name must use a-z, 0-9 and single hyphens, not at start/end")
        if name != skill_dir.resolve().name:
            errors.append(f"frontmatter: name '{name}' must match directory name '{skill_dir.resolve().name}'")
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("frontmatter: 'description' is required and must be a non-empty string")
    elif len(description) > 1024:
        errors.append(f"frontmatter: description is {len(description)} chars (max 1024)")
    elif len(description) < 80:
        warnings.append("frontmatter: description is very short; say what the skill does and when to use it")
    if "compatibility" in meta:
        compat = meta["compatibility"]
        if not isinstance(compat, str) or not 1 <= len(compat) <= 500:
            errors.append("frontmatter: compatibility must be a string of 1-500 chars")
    if "metadata" in meta:
        metadata = meta["metadata"]
        if not isinstance(metadata, dict) or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()):
            errors.append("frontmatter: metadata must map string keys to string values (quote numbers)")
    if "license" in meta and not isinstance(meta["license"], str):
        errors.append("frontmatter: license must be a string")
    if "allowed-tools" in meta and not isinstance(meta["allowed-tools"], str):
        errors.append("frontmatter: allowed-tools must be a space-separated string")


def validate_skill(skill_dir: Path) -> Dict[str, object]:
    errors: List[str] = []
    warnings: List[str] = []
    info: Dict[str, object] = {}
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {"valid": False, "errors": [f"{skill_md} not found"], "warnings": [], "info": {}}

    text = skill_md.read_text(encoding="utf-8")
    raw_meta, body = split_frontmatter(text)
    if raw_meta is None:
        errors.append("SKILL.md must start with '---' YAML frontmatter closed by '---'")
        meta: Dict = {}
    else:
        try:
            meta = yaml.safe_load(raw_meta) or {}
        except yaml.YAMLError as exc:
            errors.append(f"frontmatter: invalid YAML: {exc}")
            meta = {}
        if not isinstance(meta, dict):
            errors.append("frontmatter must be a YAML mapping")
            meta = {}
    validate_frontmatter(meta, skill_dir, errors, warnings)

    line_count = len(text.splitlines())
    body_tokens = len(body) // 4  # rough estimate: ~4 characters per token
    info.update({"name": meta.get("name"), "description_chars": len(str(meta.get("description", ""))),
                 "skill_md_lines": line_count, "body_tokens_estimate": body_tokens})
    if line_count >= MAX_LINES:
        errors.append(f"SKILL.md has {line_count} lines (keep under {MAX_LINES})")
    if body_tokens > MAX_BODY_TOKENS:
        warnings.append(f"SKILL.md body is ~{body_tokens} tokens (recommended < {MAX_BODY_TOKENS})")

    markdown_files = sorted(skill_dir.rglob("*.md"))
    errors.extend(check_markdown_links(markdown_files, confine_to=skill_dir))

    linked = {(skill_dir / t.split("#", 1)[0]).resolve() for t in iter_links(body)
              if not t.startswith(EXTERNAL_PREFIXES)}
    for ref in sorted((skill_dir / "references").glob("*")):
        if ref.is_file() and ref.resolve() not in linked:
            warnings.append(f"{ref.relative_to(skill_dir)} is not linked from SKILL.md")

    for path in sorted(p for p in skill_dir.rglob("*") if p.is_file()):
        if path.suffix in {".md", ".py", ".csv", ".json", ".yaml", ".yml", ".txt"}:
            if ABSOLUTE_PATH_RE.search(path.read_text(encoding="utf-8", errors="replace")):
                errors.append(f"{path.relative_to(skill_dir)}: contains an absolute local path")
        if path.suffix == ".py":
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")  # no __pycache__ written
            except SyntaxError as exc:
                errors.append(f"{path.relative_to(skill_dir)}: does not compile: {exc}")
    info["files"] = sum(1 for p in skill_dir.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return {"valid": not errors, "errors": errors, "warnings": warnings, "info": info}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an Agent Skill directory.")
    parser.add_argument("skill_dir", nargs="?", type=Path, default=Path("skills/intelligent-qa-engineer"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.skill_dir.is_dir():
        print(f"error: not a directory: {args.skill_dir}", file=sys.stderr)
        return 2
    result = validate_skill(args.skill_dir)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for message in result["errors"]:
            print(f"ERROR   {message}")
        for message in result["warnings"]:
            print(f"WARNING {message}")
        for key, value in result["info"].items():
            print(f"  {key}: {value}")
        print("Result: " + ("VALID" if result["valid"] else "INVALID"))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
