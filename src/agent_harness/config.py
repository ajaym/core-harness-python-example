"""Pydantic config models and TOML config loading."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from agent_harness.types import DEFAULT_TOOLS


class MCPServerConfig(BaseModel):
    """Configuration for an external MCP server."""

    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

    @field_validator("env", mode="before")
    @classmethod
    def interpolate_env_vars(cls, v: dict[str, str]) -> dict[str, str]:
        """Replace ${VAR} patterns with actual environment variable values."""
        resolved: dict[str, str] = {}
        for key, val in v.items():
            if val.startswith("${") and val.endswith("}"):
                env_name = val[2:-1]
                resolved[key] = os.environ.get(env_name, "")
            else:
                resolved[key] = val
        return resolved


class SubagentConfig(BaseModel):
    """Configuration for a subagent."""

    description: str
    prompt: str
    tools: list[str] | None = None


class HarnessConfig(BaseModel):
    """Top-level harness configuration."""

    model: str = "claude-sonnet-4-6"
    allowed_tools: list[str] = Field(default_factory=lambda: list(DEFAULT_TOOLS))
    skills_dir: Path = Path(".claude/skills")
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    permission_mode: str = "bypassPermissions"
    system_prompt: str | None = None
    subagents: dict[str, SubagentConfig] = Field(default_factory=dict)

    @field_validator("permission_mode")
    @classmethod
    def validate_permission_mode(cls, v: str) -> str:
        valid = {"default", "acceptEdits", "plan", "bypassPermissions"}
        if v not in valid:
            raise ValueError(f"permission_mode must be one of {valid}, got '{v}'")
        return v


def load_config(config_path: Path | None = None) -> HarnessConfig:
    """Load config from TOML file, with env var overrides."""
    data: dict[str, Any] = {}

    # Try to load TOML config
    if config_path is None:
        config_path = Path("harness.toml")

    if config_path.exists():
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            try:
                import tomli as tomllib  # type: ignore[no-redefine]
            except ImportError:
                import tomllib  # type: ignore[no-redefine]

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

    # Env var overrides
    if model := os.environ.get("HARNESS_MODEL"):
        data["model"] = model
    if permission_mode := os.environ.get("HARNESS_PERMISSION_MODE"):
        data["permission_mode"] = permission_mode
    if system_prompt := os.environ.get("HARNESS_SYSTEM_PROMPT"):
        data["system_prompt"] = system_prompt
    if skills_dir := os.environ.get("HARNESS_SKILLS_DIR"):
        data["skills_dir"] = skills_dir

    return HarnessConfig(**data)
