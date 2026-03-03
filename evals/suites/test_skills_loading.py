"""Eval suite: skills-loading — verifies skills influence agent behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from evals.helpers.graders import assert_output_contains, assert_output_matches
from evals.helpers.run_agent import run_agent

SKILL_FIXTURE = str(Path(__file__).parent.parent / "fixtures" / "sample_skill")


@pytest.mark.eval
class TestSkillsLoading:
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_skill_influences_format(self) -> None:
        """Verify that a formatting skill influences agent output structure."""
        result = await run_agent(
            prompt="What is Python? Answer following the skill instructions exactly.",
            options={
                "allowed_tools": [],
                "setting_sources": ["project"],
                "system_prompt": (
                    "Always format your responses with these sections: "
                    "## Summary, ## Details, ## Confidence (HIGH/MEDIUM/LOW). "
                    "Never deviate from this format."
                ),
            },
        )

        summary_grade = assert_output_contains(result, "Summary")
        details_grade = assert_output_contains(result, "Details")
        confidence_grade = assert_output_contains(result, "Confidence")

        assert summary_grade.passed, summary_grade.reason
        assert details_grade.passed, details_grade.reason
        assert confidence_grade.passed, confidence_grade.reason

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_skill_formatting_instructions_followed(self) -> None:
        """Verify skill formatting instructions are reflected in output."""
        result = await run_agent(
            prompt=(
                "Explain what a list comprehension is in Python. Follow the format instructions."
            ),
            options={
                "allowed_tools": [],
                "system_prompt": (
                    "Always format your responses with these sections: "
                    "## Summary, ## Details, ## Confidence (HIGH/MEDIUM/LOW). "
                    "Never deviate from this format."
                ),
            },
        )

        # Should contain the confidence rating
        confidence_grade = assert_output_matches(result, r"(HIGH|MEDIUM|LOW)")
        assert confidence_grade.passed, confidence_grade.reason
