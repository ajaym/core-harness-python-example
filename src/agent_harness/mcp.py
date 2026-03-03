"""MCP server config parsing and loading."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from agent_harness.config import MCPServerConfig

logger = logging.getLogger(__name__)


def interpolate_env_value(value: str) -> str:
    """Replace ${VAR} patterns with environment variable values."""
    if value.startswith("${") and value.endswith("}"):
        env_name = value[2:-1]
        return os.environ.get(env_name, "")
    return value


def load_mcp_servers_from_json(config_path: Path) -> dict[str, MCPServerConfig]:
    """Load MCP server declarations from a JSON file.

    Expected format:
    {
        "server-name": {
            "command": "npx",
            "args": ["..."],
            "env": {"KEY": "${ENV_VAR}"}
        }
    }
    """
    if not config_path.exists():
        logger.debug("MCP servers config not found: %s", config_path)
        return {}

    with open(config_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    servers: dict[str, MCPServerConfig] = {}
    for name, server_data in data.items():
        if not isinstance(server_data, dict):
            logger.warning("Skipping invalid MCP server entry: %s", name)
            continue
        if "command" not in server_data:
            raise ValueError(f"MCP server '{name}' is missing required 'command' field")
        servers[name] = MCPServerConfig(**server_data)

    logger.info("Loaded %d MCP server(s) from %s", len(servers), config_path)
    return servers


def build_mcp_server_configs(
    config_servers: dict[str, MCPServerConfig],
    json_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Build MCP server config dicts suitable for ClaudeAgentOptions.mcp_servers.

    Merges servers from the TOML config and optional JSON file.
    TOML config takes precedence over JSON file entries with the same name.
    """
    servers: dict[str, MCPServerConfig] = {}

    # Load from JSON file if provided
    if json_path is not None:
        servers.update(load_mcp_servers_from_json(json_path))

    # TOML config servers override JSON
    servers.update(config_servers)

    # Convert to SDK-compatible dicts
    result: dict[str, dict[str, Any]] = {}
    for name, server in servers.items():
        entry: dict[str, Any] = {"command": server.command}
        if server.args:
            entry["args"] = server.args
        if server.env:
            entry["env"] = server.env
        result[name] = entry

    return result
