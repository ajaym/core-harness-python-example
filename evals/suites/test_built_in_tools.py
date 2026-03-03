"""Eval suite: built-in-tools — validates agent uses SDK tools correctly."""

from __future__ import annotations

from pathlib import Path

import pytest

from evals.helpers.graders import (
    assert_file_contains,
    assert_output_contains,
    assert_tool_used,
)
from evals.helpers.run_agent import run_agent

FIXTURES_DIR = str(Path(__file__).parent.parent / "fixtures" / "sample_project")


@pytest.mark.eval
class TestBuiltInTools:
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_file_listing_uses_glob(self) -> None:
        """Agent uses Glob to list files in a directory."""
        result = await run_agent(
            prompt="List all Python files in this directory. Just list the filenames.",
            working_dir=FIXTURES_DIR,
            options={"allowed_tools": ["Glob", "Read", "Bash"]},
        )

        glob_grade = assert_tool_used(result, "Glob")
        main_grade = assert_output_contains(result, "main.py")
        utils_grade = assert_output_contains(result, "utils.py")

        assert glob_grade.passed, glob_grade.reason
        assert main_grade.passed, main_grade.reason
        assert utils_grade.passed, utils_grade.reason

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_file_read_and_summarize(self) -> None:
        """Agent reads a file and reports its contents."""
        result = await run_agent(
            prompt=(
                "Read utils.py and tell me what functions it defines. Just list the function names."
            ),
            working_dir=FIXTURES_DIR,
            options={"allowed_tools": ["Read", "Glob"]},
        )

        read_grade = assert_tool_used(result, "Read")
        content_grade = assert_output_contains(result, "format_date")

        assert read_grade.passed, read_grade.reason
        assert content_grade.passed, content_grade.reason

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_file_write_creates_file(self, tmp_path: Path) -> None:
        """Agent creates a file with specified content."""
        result = await run_agent(
            prompt='Create a file called hello.txt containing exactly "Hello, world!"',
            working_dir=str(tmp_path),
            options={"allowed_tools": ["Write"]},
        )

        write_grade = assert_tool_used(result, "Write")
        file_grade = assert_file_contains(tmp_path / "hello.txt", "Hello, world!")

        assert write_grade.passed, write_grade.reason
        assert file_grade.passed, file_grade.reason
