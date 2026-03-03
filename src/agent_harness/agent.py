"""Agent SDK initialization and execution."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, query

from agent_harness.config import HarnessConfig
from agent_harness.mcp import build_mcp_server_configs
from agent_harness.providers import ProviderConfig, get_agent_options_kwargs
from agent_harness.skills import SkillInfo
from agent_harness.tools_registry import create_custom_tools_server

logger = logging.getLogger(__name__)


def _extract_root_cause(exc: Exception, stderr_lines: list[str]) -> str:
    """Extract a user-friendly error message from SDK exceptions.

    The SDK often wraps the real error (e.g. "Credit balance is too low") inside
    opaque TaskGroup / CLIConnectionError exceptions.  We check CLI stderr output
    and the full exception chain to surface the actual cause.
    """
    # Check CLI stderr first — most reliable source
    if stderr_lines:
        meaningful = [l for l in stderr_lines if l.strip()]
        if meaningful:
            return meaningful[-1]

    # Walk the exception chain / group for an inner message
    msg = str(exc)
    if isinstance(exc, BaseExceptionGroup):
        for inner in exc.exceptions:
            inner_msg = str(inner)
            # Prefer messages that aren't just transport plumbing
            if "ProcessTransport" not in inner_msg:
                return inner_msg
            # Check __cause__
            if inner.__cause__:
                cause_msg = str(inner.__cause__)
                if "ProcessTransport" not in cause_msg:
                    return cause_msg

    # Check for "Error output:" pattern from SDK
    if "Error output:" in msg:
        parts = msg.split("Error output:")
        if len(parts) > 1:
            return parts[-1].strip()

    return msg


@dataclass(frozen=True)
class AgentResult:
    """Result of an agent execution."""

    response_text: str
    session_id: str | None
    exit_code: int


def _build_agent_options(
    config: HarnessConfig,
    provider_config: ProviderConfig,
    skills: list[SkillInfo],
    cwd: str | None = None,
    resume: str | None = None,
    permission_mode: str | None = None,
) -> ClaudeAgentOptions:
    """Assemble ClaudeAgentOptions from all resolved components."""
    kwargs = get_agent_options_kwargs(provider_config)

    # Built-in tools
    kwargs["allowed_tools"] = list(config.allowed_tools)

    # Permission mode (CLI flag overrides config)
    mode = permission_mode or config.permission_mode
    kwargs["permission_mode"] = mode

    # System prompt
    if config.system_prompt:
        kwargs["system_prompt"] = config.system_prompt

    # Working directory
    if cwd:
        kwargs["cwd"] = cwd

    # Session resumption
    if resume:
        kwargs["resume"] = resume

    # MCP servers: external (from config + JSON) + in-process
    mcp_servers: dict[str, Any] = build_mcp_server_configs(
        config.mcp_servers,
        json_path=Path("mcp-servers.json"),
    )

    # Add in-process custom tools server
    try:
        custom_server = create_custom_tools_server()
        mcp_servers["custom-tools"] = custom_server
    except ImportError:
        logger.warning(
            "claude_agent_sdk MCP server creation not available. "
            "Custom tools (lookup_user, run_query) will be unavailable."
        )
    except Exception as e:
        logger.error(
            "Failed to create custom tools MCP server: %s. "
            "Custom tools will be unavailable.",
            e,
            exc_info=True,
        )

    if mcp_servers:
        kwargs["mcp_servers"] = mcp_servers

    # Skills → setting_sources so CLAUDE.md / skills are loaded
    if skills:
        kwargs["setting_sources"] = ["project"]

    # Subagents
    if config.subagents:
        from claude_agent_sdk import AgentDefinition

        agents: dict[str, AgentDefinition] = {}
        for name, sub_config in config.subagents.items():
            agent_def = AgentDefinition(
                description=sub_config.description,
                prompt=sub_config.prompt,
            )
            if sub_config.tools is not None:
                agent_def.tools = sub_config.tools
            agents[name] = agent_def
        kwargs["agents"] = agents

    # Strip CLAUDECODE env var to allow running from within a Claude Code session.
    # The bundled CLI refuses to start if it detects a parent Claude Code process.
    # We must remove it from os.environ directly because the SDK merges os.environ
    # into the subprocess env, and the CLI checks for the variable's existence (not value).
    os.environ.pop("CLAUDECODE", None)

    return ClaudeAgentOptions(**kwargs)


async def run_agent(
    prompt: str,
    config: HarnessConfig,
    provider_config: ProviderConfig,
    skills: list[SkillInfo],
    cwd: str | None = None,
    resume: str | None = None,
    permission_mode: str | None = None,
) -> AgentResult:
    """Execute the agent with the given prompt and configuration."""
    options = _build_agent_options(
        config=config,
        provider_config=provider_config,
        skills=skills,
        cwd=cwd,
        resume=resume,
        permission_mode=permission_mode,
    )

    response_parts: list[str] = []
    session_id: str | None = None
    cli_stderr_lines: list[str] = []

    # Capture CLI stderr to surface the real error when the SDK gives opaque messages
    original_stderr = options.stderr

    def _capture_stderr(line: str) -> None:
        cli_stderr_lines.append(line.rstrip())
        if original_stderr:
            original_stderr(line)

    options.stderr = _capture_stderr

    try:
        async for message in query(prompt=prompt, options=options):
            # Try to capture session ID
            if hasattr(message, "session_id"):
                session_id = message.session_id

            # Stream content to stdout
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        sys.stdout.write(block.text)
                        sys.stdout.flush()
                        response_parts.append(block.text)

            # Handle result messages
            if (
                hasattr(message, "type")
                and message.type == "result"
                and hasattr(message, "session_id")
            ):
                session_id = message.session_id

    except KeyboardInterrupt:
        logger.info("Agent execution interrupted by user")
        raise
    except Exception as e:
        # Try to extract the real error from CLI stderr or the exception chain
        root_cause = _extract_root_cause(e, cli_stderr_lines)
        logger.error("Agent execution failed: %s", root_cause)
        return AgentResult(
            response_text=root_cause,
            session_id=session_id,
            exit_code=1,
        )

    return AgentResult(
        response_text="".join(response_parts),
        session_id=session_id,
        exit_code=0,
    )


def run_agent_sync(
    prompt: str,
    config: HarnessConfig,
    provider_config: ProviderConfig,
    skills: list[SkillInfo],
    cwd: str | None = None,
    resume: str | None = None,
    permission_mode: str | None = None,
) -> AgentResult:
    """Synchronous wrapper for run_agent."""
    return asyncio.run(
        run_agent(
            prompt=prompt,
            config=config,
            provider_config=provider_config,
            skills=skills,
            cwd=cwd,
            resume=resume,
            permission_mode=permission_mode,
        )
    )
