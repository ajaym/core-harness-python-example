"""Tests for skill directory scanning and loading."""

from __future__ import annotations

from pathlib import Path

from agent_harness.skills import SkillInfo, discover_skills


class TestDiscoverSkills:
    def test_discover_from_populated_dir(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "skill-one"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill One\nDo something.")

        skills = discover_skills(tmp_path)
        assert len(skills) == 1
        assert skills[0].name == "skill-one"
        assert skills[0].content == "# Skill One\nDo something."

    def test_discover_multiple_skills(self, tmp_path: Path) -> None:
        for name in ["alpha", "beta", "gamma"]:
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"# {name}")

        skills = discover_skills(tmp_path)
        assert len(skills) == 3
        names = [s.name for s in skills]
        assert names == ["alpha", "beta", "gamma"]  # sorted

    def test_empty_directory(self, tmp_path: Path) -> None:
        skills = discover_skills(tmp_path)
        assert skills == []

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        skills = discover_skills(tmp_path / "does-not-exist")
        assert skills == []

    def test_ignore_folders_without_skill_md(self, tmp_path: Path) -> None:
        # Folder with SKILL.md
        valid = tmp_path / "valid-skill"
        valid.mkdir()
        (valid / "SKILL.md").write_text("# Valid")

        # Folder without SKILL.md
        invalid = tmp_path / "no-skill"
        invalid.mkdir()
        (invalid / "README.md").write_text("Not a skill")

        skills = discover_skills(tmp_path)
        assert len(skills) == 1
        assert skills[0].name == "valid-skill"

    def test_ignore_files_in_skills_dir(self, tmp_path: Path) -> None:
        (tmp_path / "not-a-dir.md").write_text("file, not a skill")
        skill_dir = tmp_path / "real-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Real skill")

        skills = discover_skills(tmp_path)
        assert len(skills) == 1

    def test_skill_path_is_set(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("content")

        skills = discover_skills(tmp_path)
        assert skills[0].path == skill_dir

    def test_skills_dir_is_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "not-a-dir"
        file_path.write_text("I'm a file")

        skills = discover_skills(file_path)
        assert skills == []


class TestSkillInfo:
    def test_dataclass_fields(self) -> None:
        info = SkillInfo(name="test", path=Path("/tmp/test"), content="# Test")
        assert info.name == "test"
        assert info.path == Path("/tmp/test")
        assert info.content == "# Test"
