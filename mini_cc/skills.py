from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    name: str
    description: str
    prompt: str

    def expand(self, args: str = "") -> str:
        return self.prompt.replace("$ARGUMENTS", args)


BUILTIN_SKILLS: dict[str, Skill] = {
    "review": Skill(
        name="review",
        description="Review code changes and report issues without editing files",
        prompt="""Review the current code changes. Do not edit files.

Steps:
1. Inspect git status and diffs.
2. Find correctness, security, performance, and maintainability issues.
3. Report findings by severity with file references.

Additional focus:
$ARGUMENTS""",
    ),
    "test": Skill(
        name="test",
        description="Find and run the relevant tests, then explain results",
        prompt="""Find and run the relevant tests for this project.

If tests fail, inspect the failure and explain the likely root cause. Fix only if the user asked you to fix.

Additional instruction:
$ARGUMENTS""",
    ),
    "explain": Skill(
        name="explain",
        description="Explain code or architecture clearly and concisely",
        prompt="""Explain the requested code or architecture.

Read relevant files first. Focus on the main flow, module responsibilities, and concrete code references.

Request:
$ARGUMENTS""",
    ),
}


class SkillRegistry:
    def __init__(self, cwd: str | None = None):
        self._skills: dict[str, Skill] = dict(BUILTIN_SKILLS)
        self._load_dir(Path.home() / ".mini-cc" / "skills")
        if cwd:
            self._load_dir(Path(cwd) / ".mini-cc" / "skills")

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def expand_if_skill(self, user_input: str) -> str:
        if not user_input.startswith("/"):
            return user_input
        name, _, args = user_input[1:].partition(" ")
        skill = self.get(name.strip())
        if skill is None:
            return user_input
        return skill.expand(args.strip())

    def prompt_section(self) -> str:
        lines = ["Available skills:"]
        for skill in sorted(self._skills.values(), key=lambda s: s.name):
            lines.append(f"- /{skill.name}: {skill.description}")
        return "\n".join(lines)

    def _load_dir(self, root: Path) -> None:
        if not root.is_dir():
            return
        for path in sorted(root.glob("*/SKILL.md")):
            skill = _load_skill(path)
            if skill:
                self._skills[skill.name] = skill


def _load_skill(path: Path) -> Skill | None:
    text = path.read_text(encoding="utf-8")
    meta, body = _split_frontmatter(text)
    name = str(meta.get("name") or path.parent.name)
    description = str(meta.get("description") or "")
    return Skill(name=name, description=description, prompt=body.strip())


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not match:
        return {}, text
    raw = match.group(1)
    body = text[match.end() :]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body
