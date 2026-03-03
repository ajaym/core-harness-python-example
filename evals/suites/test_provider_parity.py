"""Eval suite: provider-parity — verifies consistent behavior across providers."""

from __future__ import annotations

import os

import pytest

from evals.helpers.graders import assert_output_contains
from evals.helpers.run_agent import run_agent


def get_providers() -> list[str]:
    """Return list of available providers for parametrize."""
    providers = ["anthropic"]
    if os.environ.get("CLAUDE_CODE_USE_BEDROCK") == "1":
        providers.append("bedrock")
    return providers


@pytest.mark.eval
class TestProviderParity:
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_simple_math_no_tools(self) -> None:
        """Agent answers a simple math question without tools."""
        result = await run_agent(
            prompt="What is 7 * 8? Reply with just the number.",
            options={"allowed_tools": []},
        )

        grade = assert_output_contains(result, "56")
        assert grade.passed, grade.reason

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_reasoning_question(self) -> None:
        """Agent answers a reasoning question correctly."""
        result = await run_agent(
            prompt="What is the capital of France? Reply with just the city name.",
            options={"allowed_tools": []},
        )

        grade = assert_output_contains(result, "Paris")
        assert grade.passed, grade.reason
