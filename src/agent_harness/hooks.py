"""Example hooks for the agent harness lifecycle events.

Hooks are Python functions that intercept agent SDK events. They are registered
via ClaudeAgentOptions.hooks and fire on specific lifecycle events.

Available hook events:
- "tool_start": Fires before a tool is executed
- "tool_end": Fires after a tool finishes
- "message": Fires when the agent produces a message
- "error": Fires on errors

Example usage in agent.py:
    from agent_harness.hooks import create_audit_logger, create_command_blocker

    hooks = {}
    if config.enable_audit_log:
        hooks.update(create_audit_logger())
    if config.block_dangerous_commands:
        hooks.update(create_command_blocker())

    options = ClaudeAgentOptions(hooks=hooks, ...)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def create_audit_logger() -> dict[str, list[dict[str, Any]]]:
    """Create a hook that logs all tool invocations for auditing.

    Returns a hooks dict suitable for ClaudeAgentOptions.hooks.
    """

    async def log_tool_use(tool_name: str, input_data: dict[str, Any], **kwargs: Any) -> None:
        logger.info("AUDIT: Tool '%s' invoked with input: %s", tool_name, input_data)

    # Hook format follows the SDK's HookMatcher pattern
    return {
        "PreToolUse": [
            {
                "matcher": {"tool_name": "*"},
                "callback": log_tool_use,
            }
        ],
    }


def create_command_blocker(
    blocked_patterns: list[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Create a hook that blocks dangerous shell commands.

    Args:
        blocked_patterns: List of command prefixes to block.
            Defaults to rm -rf, sudo, chmod 777.

    Returns a hooks dict suitable for ClaudeAgentOptions.hooks.
    """
    if blocked_patterns is None:
        blocked_patterns = ["rm -rf", "sudo ", "chmod 777", "mkfs", "dd if="]

    async def check_command(
        tool_name: str, input_data: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any] | None:
        if tool_name != "Bash":
            return None

        command = input_data.get("command", "")
        for pattern in blocked_patterns:
            if pattern in command:
                logger.warning("BLOCKED: Dangerous command detected: %s", command)
                return {"behavior": "deny", "message": f"Command blocked: contains '{pattern}'"}

        return None

    return {
        "PreToolUse": [
            {
                "matcher": {"tool_name": "Bash"},
                "callback": check_command,
            }
        ],
    }


def create_readonly_approver() -> dict[str, list[dict[str, Any]]]:
    """Create a hook that auto-approves read-only tools and blocks write operations.

    Returns a hooks dict suitable for ClaudeAgentOptions.hooks.
    """
    read_only_tools = {"Read", "Glob", "Grep", "WebSearch", "WebFetch"}
    write_tools = {"Write", "Edit", "Bash"}

    async def approve_reads(
        tool_name: str, input_data: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any] | None:
        if tool_name in read_only_tools:
            return {"behavior": "allow", "updated_input": input_data}
        if tool_name in write_tools:
            logger.info("READ-ONLY: Blocking write tool '%s'", tool_name)
            msg = f"Write tool '{tool_name}' not allowed in read-only mode"
            return {"behavior": "deny", "message": msg}
        return None

    return {
        "PreToolUse": [
            {
                "matcher": {"tool_name": "*"},
                "callback": approve_reads,
            }
        ],
    }
