"""Agent SDK initialization and execution."""

from __future__ import annotations

import asyncio
import logging
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


@dataclass
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
    except Exception:
        logger.warning("Failed to create in-process MCP server, skipping", exc_info=True)

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

    except Exception as e:
        logger.error("Agent execution failed: %s", e)
        return AgentResult(
            response_text=str(e),
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
