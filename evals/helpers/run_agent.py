"""Wraps SDK query() for eval context."""

from __future__ import annotations

import time
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, query

from evals.helpers.types import EvalResult


async def run_agent(
    prompt: str,
    working_dir: str | None = None,
    options: dict[str, Any] | None = None,
) -> EvalResult:
    """Run the agent with the given prompt and return an EvalResult.

    Args:
        prompt: The prompt to send to the agent.
        working_dir: Optional working directory for file operations.
        options: Optional overrides for agent options (allowed_tools, etc.)

    Returns:
        EvalResult with response text, tool calls, duration, and exit code.
    """
    agent_options_kwargs: dict[str, Any] = {
        "permission_mode": "bypassPermissions",
    }

    if working_dir:
        agent_options_kwargs["cwd"] = working_dir

    if options:
        if "allowed_tools" in options:
            agent_options_kwargs["allowed_tools"] = options["allowed_tools"]
        if "mcp_servers" in options:
            agent_options_kwargs["mcp_servers"] = options["mcp_servers"]
        if "system_prompt" in options:
            agent_options_kwargs["system_prompt"] = options["system_prompt"]
        if "setting_sources" in options:
            agent_options_kwargs["setting_sources"] = options["setting_sources"]
        if "model" in options:
            agent_options_kwargs["model"] = options["model"]

    agent_options = ClaudeAgentOptions(**agent_options_kwargs)

    response_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    errors: list[str] = []
    exit_code = 0

    start_time = time.monotonic()

    try:
        async for message in query(prompt=prompt, options=agent_options):
            # Capture text content
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        response_parts.append(block.text)
                    if hasattr(block, "type") and block.type == "tool_use":
                        tool_calls.append(
                            {
                                "name": getattr(block, "name", ""),
                                "input": getattr(block, "input", {}),
                            }
                        )

            # Capture tool results
            if (
                hasattr(message, "type")
                and message.type == "tool_result"
                and hasattr(message, "content")
            ):
                for block in message.content:
                    if hasattr(block, "text"):
                        last_tool = tool_calls[-1] if tool_calls else None
                        if last_tool:
                            last_tool["output"] = block.text

    except Exception as e:
        errors.append(str(e))
        exit_code = 1

    duration = time.monotonic() - start_time

    return EvalResult(
        response_text="".join(response_parts),
        tool_calls=tool_calls,
        duration_seconds=duration,
        exit_code=exit_code,
        errors=errors,
    )
