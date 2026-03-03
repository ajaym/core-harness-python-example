"""Eval result and grading types."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalResult:
    """Result of an agent evaluation run."""

    response_text: str
    tool_calls: list[dict[str, Any]]
    duration_seconds: float
    exit_code: int
    errors: list[str] = field(default_factory=list)


@dataclass
class GradeResult:
    """Result of a single grading check."""

    passed: bool
    score: float | None = None
    reason: str = ""


@dataclass
class EvalGrader:
    """A grading function for an eval task."""

    name: str
    type: str  # "code" or "model"
    fn: Callable[[EvalResult], Awaitable[GradeResult]]


@dataclass
class EvalTask:
    """Definition of an eval task."""

    name: str
    suite: str
    tags: list[str]
    prompt: str
    graders: list[EvalGrader]
    working_dir: str | None = None
    options: dict[str, Any] | None = None
    timeout: float = 60.0
    trials: int = 1
    cost_tier: str = "low"
