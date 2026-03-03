"""Eval-specific pytest configuration."""

from __future__ import annotations

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "eval: mark test as an LLM eval")
    config.addinivalue_line("markers", "slow: mark test as slow-running")


@pytest.fixture(autouse=True)
def require_api_key() -> None:
    """Skip eval tests if no API key is set."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY required for evals")


@pytest.fixture
def eval_timeout() -> float:
    """Default timeout for eval tasks: 120 seconds."""
    return 120.0
