"""Tests for provider detection and validation."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from agent_harness.providers import (
    ProviderError,
    detect_provider,
    get_agent_options_kwargs,
    resolve_provider,
    validate_anthropic_credentials,
    validate_bedrock_credentials,
)


class TestDetectProvider:
    def test_default_is_anthropic(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLAUDE_CODE_USE_BEDROCK", None)
            assert detect_provider() == "anthropic"

    def test_bedrock_when_env_set(self) -> None:
        with patch.dict(os.environ, {"CLAUDE_CODE_USE_BEDROCK": "1"}):
            assert detect_provider() == "bedrock"

    def test_anthropic_when_bedrock_not_one(self) -> None:
        with patch.dict(os.environ, {"CLAUDE_CODE_USE_BEDROCK": "0"}):
            assert detect_provider() == "anthropic"


class TestValidateAnthropicCredentials:
    def test_valid_key(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
            creds = validate_anthropic_credentials()
        assert creds["ANTHROPIC_API_KEY"] == "sk-ant-test123"

    def test_missing_key_raises(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(ProviderError, match="ANTHROPIC_API_KEY"):
                validate_anthropic_credentials()


class TestValidateBedrockCredentials:
    def test_valid_credentials(self) -> None:
        with patch.dict(
            os.environ,
            {
                "AWS_REGION": "us-east-1",
                "AWS_ACCESS_KEY_ID": "AKIATEST",
                "AWS_SECRET_ACCESS_KEY": "secret",
            },
        ):
            creds = validate_bedrock_credentials()
        assert creds["AWS_REGION"] == "us-east-1"
        assert creds["AWS_ACCESS_KEY_ID"] == "AKIATEST"
        assert creds["AWS_SECRET_ACCESS_KEY"] == "secret"
        assert creds["CLAUDE_CODE_USE_BEDROCK"] == "1"

    def test_missing_all_credentials(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("AWS_REGION", None)
            os.environ.pop("AWS_ACCESS_KEY_ID", None)
            os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
            with pytest.raises(ProviderError, match="AWS_REGION"):
                validate_bedrock_credentials()

    def test_missing_partial_credentials(self) -> None:
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            os.environ.pop("AWS_ACCESS_KEY_ID", None)
            os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
            with pytest.raises(ProviderError, match="AWS_ACCESS_KEY_ID"):
                validate_bedrock_credentials()


class TestResolveProvider:
    def test_resolve_anthropic(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=True):
            os.environ.pop("CLAUDE_CODE_USE_BEDROCK", None)
            config = resolve_provider("claude-sonnet-4-6")
        assert config.provider == "anthropic"
        assert config.model == "claude-sonnet-4-6"

    def test_resolve_bedrock(self) -> None:
        with patch.dict(
            os.environ,
            {
                "CLAUDE_CODE_USE_BEDROCK": "1",
                "AWS_REGION": "us-west-2",
                "AWS_ACCESS_KEY_ID": "AKIA",
                "AWS_SECRET_ACCESS_KEY": "secret",
            },
        ):
            config = resolve_provider("claude-sonnet-4-6")
        assert config.provider == "bedrock"
        assert config.env["AWS_REGION"] == "us-west-2"

    def test_model_propagation(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=True):
            os.environ.pop("CLAUDE_CODE_USE_BEDROCK", None)
            config = resolve_provider("claude-opus-4-6")
        assert config.model == "claude-opus-4-6"

    def test_missing_anthropic_key_raises(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            os.environ.pop("CLAUDE_CODE_USE_BEDROCK", None)
            with pytest.raises(ProviderError):
                resolve_provider("claude-sonnet-4-6")


class TestGetAgentOptionsKwargs:
    def test_returns_model_and_env(self) -> None:
        from agent_harness.providers import ProviderConfig

        config = ProviderConfig(
            provider="anthropic",
            model="claude-sonnet-4-6",
            env={"ANTHROPIC_API_KEY": "sk-test"},
        )
        kwargs = get_agent_options_kwargs(config)
        assert kwargs["model"] == "claude-sonnet-4-6"
        assert kwargs["env"]["ANTHROPIC_API_KEY"] == "sk-test"
