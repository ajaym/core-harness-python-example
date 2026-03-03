"""Shared type aliases for the agent harness."""

from __future__ import annotations

from typing import Literal

ToolName = Literal[
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "WebSearch",
    "WebFetch",
]

DEFAULT_TOOLS: list[str] = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]

PermissionModeType = Literal["default", "acceptEdits", "plan", "bypassPermissions"]

ProviderType = Literal["anthropic", "bedrock"]
