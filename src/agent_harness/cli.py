"""Click-based CLI entry point for the agent harness."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import click
from dotenv import load_dotenv

from agent_harness.agent import run_agent_sync
from agent_harness.config import load_config
from agent_harness.providers import ProviderError, resolve_provider
from agent_harness.skills import discover_skills


@click.command()
@click.option("--prompt", required=True, help="The prompt to send to the agent.")
@click.option(
    "--cwd",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Working directory for agent file operations.",
)
@click.option(
    "--output",
    "output_format",
    default="text",
    type=click.Choice(["text", "json"]),
    help="Output format: text or json.",
)
@click.option("--resume", default=None, help="Resume a previous session by ID.")
@click.option(
    "--permission-mode",
    default=None,
    type=click.Choice(["default", "acceptEdits", "bypassPermissions", "plan"]),
    help="Permission mode for agent operations.",
)
@click.option(
    "--config",
    "config_path",
    default=None,
    type=click.Path(exists=False),
    help="Path to harness.toml config file.",
)
def main(
    prompt: str,
    cwd: str | None,
    output_format: str,
    resume: str | None,
    permission_mode: str | None,
    config_path: str | None,
) -> None:
    """Agent Harness — Run a Claude-powered agent from the CLI."""
    # Load .env file
    load_dotenv()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Load config
    try:
        config = load_config(Path(config_path) if config_path else None)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)

    # Resolve provider
    try:
        provider_config = resolve_provider(config.model)
    except ProviderError as e:
        click.echo(f"Provider error: {e}", err=True)
        sys.exit(1)

    # Discover skills
    skills = discover_skills(config.skills_dir)

    # Print session info
    if resume:
        logger.info("Resuming session: %s", resume)
    logger.info("Provider: %s | Model: %s", provider_config.provider, provider_config.model)

    # Run the agent
    result = run_agent_sync(
        prompt=prompt,
        config=config,
        provider_config=provider_config,
        skills=skills,
        cwd=cwd,
        resume=resume,
        permission_mode=permission_mode,
    )

    # Output results
    if output_format == "json":
        output = {
            "type": "result",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "response_text": result.response_text,
                "session_id": result.session_id,
                "exit_code": result.exit_code,
            },
        }
        click.echo(json.dumps(output))
    else:
        # Text output was already streamed during execution
        if result.session_id:
            click.echo(f"\nSession ID: {result.session_id}", err=True)

    sys.exit(result.exit_code)
