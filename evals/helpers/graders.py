"""Code-based grader utilities for eval assertions."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, ValidationError

from evals.helpers.types import EvalResult, GradeResult


def assert_output_contains(result: EvalResult, substring: str) -> GradeResult:
    """Assert the agent's response contains the expected substring (case-insensitive)."""
    found = substring.lower() in result.response_text.lower()
    return GradeResult(
        passed=found,
        score=1.0 if found else 0.0,
        reason=f"Found '{substring}' in output" if found else f"'{substring}' not found in output",
    )


def assert_output_matches(result: EvalResult, pattern: str) -> GradeResult:
    """Assert the agent's response matches a regex pattern."""
    match = re.search(pattern, result.response_text, re.IGNORECASE)
    passed = match is not None
    return GradeResult(
        passed=passed,
        score=1.0 if passed else 0.0,
        reason=f"Pattern '{pattern}' matched" if passed else f"Pattern '{pattern}' did not match",
    )


def assert_tool_used(result: EvalResult, tool_name: str, count: int | None = None) -> GradeResult:
    """Assert the agent invoked a specific tool, optionally a specific number of times."""
    tool_uses = [tc for tc in result.tool_calls if tc.get("name") == tool_name]
    used = len(tool_uses) > 0

    if count is not None:
        passed = len(tool_uses) == count
        return GradeResult(
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=f"{tool_name} called {len(tool_uses)} time(s), expected {count}",
        )

    return GradeResult(
        passed=used,
        score=1.0 if used else 0.0,
        reason=f"{tool_name} called {len(tool_uses)} time(s)"
        if used
        else f"{tool_name} was not used",
    )


def assert_tool_not_used(result: EvalResult, tool_name: str) -> GradeResult:
    """Assert the agent did not invoke a specific tool."""
    tool_uses = [tc for tc in result.tool_calls if tc.get("name") == tool_name]
    not_used = len(tool_uses) == 0
    return GradeResult(
        passed=not_used,
        score=1.0 if not_used else 0.0,
        reason=f"{tool_name} was not used"
        if not_used
        else f"{tool_name} was used {len(tool_uses)} time(s)",
    )


def assert_file_exists(file_path: str | Path) -> GradeResult:
    """Assert a file was created at the expected path."""
    exists = Path(file_path).exists()
    return GradeResult(
        passed=exists,
        score=1.0 if exists else 0.0,
        reason=f"File exists: {file_path}" if exists else f"File not found: {file_path}",
    )


def assert_file_contains(file_path: str | Path, substring: str) -> GradeResult:
    """Assert a file exists and its content includes the expected substring."""
    path = Path(file_path)
    if not path.exists():
        return GradeResult(passed=False, score=0.0, reason=f"File not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    found = substring in content
    return GradeResult(
        passed=found,
        score=1.0 if found else 0.0,
        reason=f"Found '{substring}' in {file_path}"
        if found
        else f"'{substring}' not found in {file_path}",
    )


def assert_json_schema(result: EvalResult, model: type[BaseModel]) -> GradeResult:
    """Validate the agent's output against a Pydantic model."""
    import json

    try:
        data = json.loads(result.response_text)
        model.model_validate(data)
        return GradeResult(passed=True, score=1.0, reason="Output matches schema")
    except (json.JSONDecodeError, ValidationError) as e:
        return GradeResult(passed=False, score=0.0, reason=f"Schema validation failed: {e}")


def assert_exit_code(result: EvalResult, code: int) -> GradeResult:
    """Assert the agent exited with the expected code."""
    passed = result.exit_code == code
    return GradeResult(
        passed=passed,
        score=1.0 if passed else 0.0,
        reason=f"Exit code: {result.exit_code}, expected: {code}",
    )
