"""Model-based grader using Claude to score agent output."""

from __future__ import annotations

import json
import os

from evals.helpers.types import EvalResult, GradeResult


async def grade_with_model(
    result: EvalResult,
    rubric: str,
    model: str | None = None,
) -> GradeResult:
    """Send the agent's output plus a rubric to Claude for scoring.

    Args:
        result: The eval result to grade.
        rubric: Natural-language rubric describing what constitutes a good response.
        model: Optional model override (defaults to claude-sonnet-4-6).

    Returns:
        GradeResult with score (1-5) and explanation.
    """
    try:
        import anthropic
    except ImportError:
        return GradeResult(
            passed=False,
            score=None,
            reason="anthropic package not installed — cannot use model grader",
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return GradeResult(
            passed=False,
            score=None,
            reason="ANTHROPIC_API_KEY not set — cannot use model grader",
        )

    client = anthropic.AsyncAnthropic(api_key=api_key)

    grading_prompt = f"""You are an eval grader. Score the following agent output on a scale of 1-5.

## Rubric
{rubric}

## Agent Output
{result.response_text}

## Tools Used
{json.dumps([tc.get("name", "") for tc in result.tool_calls])}

Respond with a JSON object containing:
- "score": integer from 1 to 5
- "explanation": brief explanation of the score

Only output the JSON object, nothing else."""

    response = await client.messages.create(
        model=model or "claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": grading_prompt}],
    )

    response_text = response.content[0].text  # type: ignore[union-attr]

    try:
        grade_data = json.loads(response_text)
        score = int(grade_data["score"])
        explanation = grade_data.get("explanation", "")
        return GradeResult(
            passed=score >= 3,
            score=float(score),
            reason=explanation,
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return GradeResult(
            passed=False,
            score=None,
            reason=f"Failed to parse model grader response: {e}",
        )
