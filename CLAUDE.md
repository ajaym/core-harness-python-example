# CLAUDE.md — Project Context

## What This Is

Python Agent Harness — a reference implementation for building Claude-powered agents using the Python Agent SDK (`claude-agent-sdk`). CLI-driven, with dual provider support (Anthropic API / AWS Bedrock), MCP server integration (external + in-process), Agent Skills, and a comprehensive test + eval framework.

## Quick Commands

```bash
pip install -e ".[dev]"           # Install in dev mode
pytest tests/                      # Unit tests (62 tests, no API key needed)
pytest evals/                      # LLM evals (requires ANTHROPIC_API_KEY)
python -m mypy src/ --strict       # Type checking
ruff check src/ tests/ evals/      # Linting
ruff format src/ tests/ evals/     # Formatting
python -m agent_harness --prompt "..." # Run the agent
```

## Architecture

- `src/agent_harness/` — Main package (cli, config, agent, providers, skills, mcp, tools_registry, hooks, types)
- `tests/` — Unit tests (pytest, mocked, no network)
- `evals/` — LLM eval framework (helpers, suites, fixtures)
- `harness.toml` — Unified TOML config (Pydantic-validated)
- `mcp-servers.json` — External MCP server declarations

## Key Patterns

- **Config**: Pydantic v2 models in `config.py`, loaded from TOML with env var overrides
- **CLI**: Click-based in `cli.py`, entry point `agent-harness` in pyproject.toml
- **Providers**: Env-driven detection in `providers.py` (ANTHROPIC_API_KEY vs CLAUDE_CODE_USE_BEDROCK=1)
- **Tools**: In-process MCP via `@tool` decorator in `tools_registry.py`
- **Skills**: Folder-based discovery in `skills.py` (.claude/skills/*/SKILL.md)
- **Tests**: All external deps mocked, no API calls in unit tests

## Style

- Python 3.10+, src layout, hatchling build
- `from __future__ import annotations` in all files
- mypy --strict, ruff for lint/format
- Line length: 100
