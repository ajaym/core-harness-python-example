"""Tests for MCP server config parsing and loading."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_harness.config import MCPServerConfig
from agent_harness.mcp import (
    build_mcp_server_configs,
    interpolate_env_value,
    load_mcp_servers_from_json,
)


class TestInterpolateEnvValue:
    def test_interpolate_existing_var(self) -> None:
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            assert interpolate_env_value("${MY_VAR}") == "hello"

    def test_interpolate_missing_var(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MISSING", None)
            assert interpolate_env_value("${MISSING}") == ""

    def test_literal_value_unchanged(self) -> None:
        assert interpolate_env_value("literal") == "literal"

    def test_partial_interpolation_not_replaced(self) -> None:
        assert interpolate_env_value("prefix${VAR}") == "prefix${VAR}"


class TestLoadMCPServersFromJson:
    def test_valid_json(self, tmp_path: Path) -> None:
        config_file = tmp_path / "mcp.json"
        config_file.write_text(
            json.dumps(
                {
                    "test-server": {
                        "command": "npx",
                        "args": ["-y", "server"],
                    }
                }
            )
        )

        servers = load_mcp_servers_from_json(config_file)
        assert "test-server" in servers
        assert servers["test-server"].command == "npx"
        assert servers["test-server"].args == ["-y", "server"]

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        servers = load_mcp_servers_from_json(tmp_path / "nonexistent.json")
        assert servers == {}

    def test_missing_command_raises(self, tmp_path: Path) -> None:
        config_file = tmp_path / "bad.json"
        config_file.write_text(json.dumps({"bad": {"args": ["something"]}}))

        with pytest.raises(ValueError, match="missing required 'command' field"):
            load_mcp_servers_from_json(config_file)

    def test_env_interpolation_in_json(self, tmp_path: Path) -> None:
        config_file = tmp_path / "mcp.json"
        config_file.write_text(
            json.dumps(
                {
                    "github": {
                        "command": "npx",
                        "env": {"TOKEN": "${GH_TOKEN}"},
                    }
                }
            )
        )

        with patch.dict(os.environ, {"GH_TOKEN": "ghp_test"}):
            servers = load_mcp_servers_from_json(config_file)
        assert servers["github"].env["TOKEN"] == "ghp_test"

    def test_multiple_servers(self, tmp_path: Path) -> None:
        config_file = tmp_path / "mcp.json"
        config_file.write_text(
            json.dumps(
                {
                    "server-a": {"command": "cmd-a"},
                    "server-b": {"command": "cmd-b", "args": ["--flag"]},
                }
            )
        )

        servers = load_mcp_servers_from_json(config_file)
        assert len(servers) == 2
        assert servers["server-a"].command == "cmd-a"
        assert servers["server-b"].args == ["--flag"]


class TestBuildMCPServerConfigs:
    def test_empty_configs(self) -> None:
        result = build_mcp_server_configs({})
        assert result == {}

    def test_config_servers_only(self) -> None:
        servers = {"test": MCPServerConfig(command="npx", args=["server"])}
        result = build_mcp_server_configs(servers)
        assert "test" in result
        assert result["test"]["command"] == "npx"
        assert result["test"]["args"] == ["server"]

    def test_json_and_config_merge(self, tmp_path: Path) -> None:
        json_file = tmp_path / "mcp.json"
        json_file.write_text(json.dumps({"json-server": {"command": "from-json"}}))

        config_servers = {"config-server": MCPServerConfig(command="from-config")}
        result = build_mcp_server_configs(config_servers, json_path=json_file)

        assert "json-server" in result
        assert "config-server" in result

    def test_config_overrides_json(self, tmp_path: Path) -> None:
        json_file = tmp_path / "mcp.json"
        json_file.write_text(json.dumps({"shared": {"command": "from-json"}}))

        config_servers = {"shared": MCPServerConfig(command="from-config")}
        result = build_mcp_server_configs(config_servers, json_path=json_file)

        assert result["shared"]["command"] == "from-config"

    def test_empty_env_not_included(self) -> None:
        servers = {"test": MCPServerConfig(command="cmd")}
        result = build_mcp_server_configs(servers)
        assert "env" not in result["test"]
