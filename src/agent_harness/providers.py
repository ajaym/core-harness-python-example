"""Provider detection and validation (Anthropic API vs AWS Bedrock)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from agent_harness.types import ProviderType


class ProviderError(Exception):
    """Raised when provider configuration is invalid."""


@dataclass
class ProviderConfig:
    """Resolved provider configuration."""

    provider: ProviderType
    model: str
    env: dict[str, str]


def detect_provider() -> ProviderType:
    """Detect which provider to use based on environment variables."""
    if os.environ.get("CLAUDE_CODE_USE_BEDROCK") == "1":
        return "bedrock"
    return "anthropic"


def validate_anthropic_credentials() -> dict[str, str]:
    """Validate and return Anthropic API credentials."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ProviderError(
            "ANTHROPIC_API_KEY environment variable is required for the Anthropic provider. "
            "Set it in your .env file or environment."
        )
    return {"ANTHROPIC_API_KEY": api_key}


def validate_bedrock_credentials() -> dict[str, str]:
    """Validate and return AWS Bedrock credentials."""
    region = os.environ.get("AWS_REGION")
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")

    missing: list[str] = []
    if not region:
        missing.append("AWS_REGION")
    if not access_key:
        missing.append("AWS_ACCESS_KEY_ID")
    if not secret_key:
        missing.append("AWS_SECRET_ACCESS_KEY")

    if missing:
        raise ProviderError(
            f"Missing required Bedrock credentials: {', '.join(missing)}. "
            "Set these in your .env file or environment."
        )

    env: dict[str, str] = {
        "CLAUDE_CODE_USE_BEDROCK": "1",
        "AWS_REGION": region,  # type: ignore[dict-item]
        "AWS_ACCESS_KEY_ID": access_key,  # type: ignore[dict-item]
        "AWS_SECRET_ACCESS_KEY": secret_key,  # type: ignore[dict-item]
    }
    return env


def resolve_provider(model: str) -> ProviderConfig:
    """Resolve and validate the provider configuration."""
    provider = detect_provider()

    if provider == "bedrock":
        env = validate_bedrock_credentials()
        # TODO: verify Bedrock connectivity in staging
    else:
        env = validate_anthropic_credentials()

    return ProviderConfig(provider=provider, model=model, env=env)


def get_agent_options_kwargs(provider_config: ProviderConfig) -> dict[str, Any]:
    """Build kwargs for ClaudeAgentOptions from provider config."""
    kwargs: dict[str, Any] = {
        "model": provider_config.model,
        "env": provider_config.env,
    }
    return kwargs
