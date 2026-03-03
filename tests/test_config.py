"""Tests for config loading and validation."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_harness.config import HarnessConfig, MCPServerConfig, load_config


class TestMCPServerConfig:
    def test_basic_config(self) -> None:
        config = MCPServerConfig(command="npx", args=["-y", "server"])
        assert config.command == "npx"
        assert config.args == ["-y", "server"]
        assert config.env == {}

    def test_env_interpolation(self) -> None:
        with patch.dict(os.environ, {"MY_TOKEN": "secret123"}):
            config = MCPServerConfig(
                command="npx",
                env={"TOKEN": "${MY_TOKEN}"},
            )
        assert config.env["TOKEN"] == "secret123"

    def test_env_interpolation_missing_var(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("NONEXISTENT_VAR", None)
            config = MCPServerConfig(
                command="npx",
                env={"TOKEN": "${NONEXISTENT_VAR}"},
            )
        assert config.env["TOKEN"] == ""

    def test_env_literal_value(self) -> None:
        config = MCPServerConfig(
            command="npx",
            env={"KEY": "literal-value"},
        )
        assert config.env["KEY"] == "literal-value"


class TestHarnessConfig:
    def test_defaults(self) -> None:
        config = HarnessConfig()
        assert config.model == "claude-sonnet-4-6"
        assert config.allowed_tools == ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
        assert config.skills_dir == Path(".claude/skills")
        assert config.permission_mode == "bypassPermissions"
        assert config.system_prompt is None
        assert config.mcp_servers == {}

    def test_custom_values(self) -> None:
        config = HarnessConfig(
            model="claude-haiku-4-5",
            allowed_tools=["Read", "Glob"],
            permission_mode="default",
            system_prompt="Be helpful.",
        )
        assert config.model == "claude-haiku-4-5"
        assert config.allowed_tools == ["Read", "Glob"]
        assert config.permission_mode == "default"
        assert config.system_prompt == "Be helpful."

    def test_invalid_permission_mode(self) -> None:
        with pytest.raises(ValueError, match="permission_mode must be one of"):
            HarnessConfig(permission_mode="invalid")

    def test_valid_permission_modes(self) -> None:
        for mode in ("default", "acceptEdits", "plan", "bypassPermissions"):
            config = HarnessConfig(permission_mode=mode)
            assert config.permission_mode == mode

    def test_mcp_servers_config(self) -> None:
        config = HarnessConfig(
            mcp_servers={
                "test": MCPServerConfig(command="npx", args=["server"]),
            }
        )
        assert "test" in config.mcp_servers
        assert config.mcp_servers["test"].command == "npx"

    def test_subagents_config(self) -> None:
        from agent_harness.config import SubagentConfig

        config = HarnessConfig(
            subagents={
                "reviewer": SubagentConfig(
                    description="Code reviewer",
                    prompt="Review code",
                    tools=["Read", "Grep"],
                ),
            }
        )
        assert "reviewer" in config.subagents
        assert config.subagents["reviewer"].tools == ["Read", "Grep"]


class TestLoadConfig:
    def test_load_defaults_no_file(self, tmp_path: Path) -> None:
        config = load_config(tmp_path / "nonexistent.toml")
        assert config.model == "claude-sonnet-4-6"
        assert config.allowed_tools == ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]

    def test_load_from_toml(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "test.toml"
        toml_file.write_text(
            'model = "claude-haiku-4-5"\nallowed_tools = ["Read"]\npermission_mode = "default"\n'
        )
        config = load_config(toml_file)
        assert config.model == "claude-haiku-4-5"
        assert config.allowed_tools == ["Read"]
        assert config.permission_mode == "default"

    def test_env_var_overrides(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "test.toml"
        toml_file.write_text('model = "claude-haiku-4-5"\n')

        with patch.dict(os.environ, {"HARNESS_MODEL": "claude-opus-4-6"}):
            config = load_config(toml_file)
        assert config.model == "claude-opus-4-6"

    def test_env_var_override_permission_mode(self) -> None:
        with patch.dict(os.environ, {"HARNESS_PERMISSION_MODE": "plan"}):
            config = load_config(Path("nonexistent.toml"))
        assert config.permission_mode == "plan"

    def test_env_var_override_system_prompt(self) -> None:
        with patch.dict(os.environ, {"HARNESS_SYSTEM_PROMPT": "Custom prompt"}):
            config = load_config(Path("nonexistent.toml"))
        assert config.system_prompt == "Custom prompt"

    def test_load_toml_with_mcp_servers(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "test.toml"
        toml_file.write_text('[mcp_servers.test]\ncommand = "npx"\nargs = ["-y", "server"]\n')
        config = load_config(toml_file)
        assert "test" in config.mcp_servers
        assert config.mcp_servers["test"].command == "npx"

    def test_malformed_toml_raises(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "bad.toml"
        toml_file.write_text("this is not valid toml {{{")
        with pytest.raises((ValueError, KeyError, TypeError, OSError)):
            load_config(toml_file)
