"""Skill directory scanning and loading."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SkillInfo:
    """Information about a discovered skill."""

    name: str
    path: Path
    content: str


def discover_skills(skills_dir: Path) -> list[SkillInfo]:
    """Scan a directory for skill folders containing SKILL.md files.

    Each skill is a subfolder of skills_dir containing a SKILL.md file.
    Returns a list of SkillInfo with the skill name, path, and content.
    """
    skills: list[SkillInfo] = []

    if not skills_dir.exists():
        logger.debug("Skills directory does not exist: %s", skills_dir)
        return skills

    if not skills_dir.is_dir():
        logger.warning("Skills path is not a directory: %s", skills_dir)
        return skills

    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir():
            continue
        skill_file = entry / "SKILL.md"
        if not skill_file.exists():
            logger.debug("Skipping %s — no SKILL.md found", entry.name)
            continue
        content = skill_file.read_text(encoding="utf-8")
        skill = SkillInfo(name=entry.name, path=entry, content=content)
        skills.append(skill)
        logger.info("Discovered skill: %s (%s)", skill.name, skill.path)

    if skills:
        logger.info("Loaded %d skill(s): %s", len(skills), ", ".join(s.name for s in skills))
    else:
        logger.debug("No skills found in %s", skills_dir)

    return skills
