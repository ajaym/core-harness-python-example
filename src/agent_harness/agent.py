"""Agent SDK initialization and execution."""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, query

from agent_harness.config import HarnessConfig
from agent_harness.mcp import build_mcp_server_configs
from agent_harness.providers import ProviderConfig, get_agent_options_kwargs
from agent_harness.skills import SkillInfo

logger = logging.getLogger(__name__)


def _extract_root_cause(exc: Exception, options: ClaudeAgentOptions) -> str:
    """Extract a user-friendly error message from SDK exceptions.

    The SDK often wraps the real error (e.g. "Credit balance is too low") inside
    opaque TaskGroup / CLIConnectionError exceptions.  The SDK's async stderr
    capture races with process exit, so on failure we re-run the CLI briefly
    with subprocess to capture the real stderr synchronously.
    """
    # Walk the exception chain / group for a meaningful inner message first
    msg = str(exc)
    if isinstance(exc, BaseExceptionGroup):
        for inner in exc.exceptions:
            inner_msg = str(inner)
            if "ProcessTransport" not in inner_msg:
                return inner_msg
            if inner.__cause__:
                cause_msg = str(inner.__cause__)
                if "ProcessTransport" not in cause_msg:
                    return cause_msg

    # If we only got opaque transport errors, run the CLI directly to get real stderr
    if "ProcessTransport" in msg or "TaskGroup" in msg:
        cli_error = _probe_cli_error(options)
        if cli_error:
            return cli_error

    return msg


def _find_bundled_cli() -> str | None:
    """Find the bundled Claude CLI binary path."""
    import platform

    cli_name = "claude.exe" if platform.system() == "Windows" else "claude"
    bundled = Path(__file__).parent / ".." / ".."  # won't work, use SDK path
    try:
        import claude_agent_sdk

        sdk_dir = Path(claude_agent_sdk.__file__).parent
        bundled_path = sdk_dir / "_bundled" / cli_name
        if bundled_path.exists():
            return str(bundled_path)
    except Exception:
        pass
    return None


def _probe_cli_error(options: ClaudeAgentOptions) -> str | None:
    """Run the CLI briefly to capture its stderr on failure.

    This is called only after the SDK gives an opaque error, to surface
    the real reason the CLI process exited (e.g. billing, auth, version issues).
    """
    try:
        cli_path = _find_bundled_cli()
        if not cli_path:
            return None

        env = {**os.environ, **options.env, "CLAUDE_CODE_ENTRYPOINT": "sdk-py"}
        result = subprocess.run(
            [cli_path, "-p", "test", "--output-format", "stream-json",
             "--input-format", "stream-json",
             "--permission-mode", options.permission_mode or "default",
             "--model", options.model],
            capture_output=True, text=True, timeout=15, env=env, input="",
        )
        if result.returncode != 0:
            # Check both stderr and stdout for error messages
            error_text = (result.stderr + "\n" + result.stdout).strip()
            if error_text:
                lines = [l for l in error_text.splitlines() if l.strip()]
                return lines[-1] if lines else error_text
    except Exception as e:
        logger.debug("CLI probe failed: %s", e)
    return None


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

    # In-process MCP servers (via create_sdk_mcp_server) are currently incompatible
    # with the bundled CLI v2.1.59 — the CLI exits before the SDK can complete the
    # MCP control handshake, causing a "ProcessTransport is not ready" error.
    # Uncomment the block below once the SDK/CLI compatibility is resolved.
    #
    # try:
    #     custom_server = create_custom_tools_server()
    #     mcp_servers["custom-tools"] = custom_server
    # except ImportError:
    #     logger.warning("claude_agent_sdk MCP server creation not available.")
    # except Exception as e:
    #     logger.error("Failed to create custom tools MCP server: %s", e)

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
        root_cause = _extract_root_cause(e, options)
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
