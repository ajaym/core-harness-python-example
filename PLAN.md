# Implementation Plan: Python Agent Harness

**Source PRD:** [PRD-agent-harness-python.md](./PRD-agent-harness-python.md) (v1.0)
**Reference Implementation:** [TypeScript Agent Harness](../core-harness-example/)
**Plan Status:** In Progress
**Last Updated:** 2026-03-02

---

## Overview

This plan implements the Python Agent Harness reference implementation as described in the PRD. The harness provides a CLI-driven foundation for building Claude-powered agents using the Python Agent SDK (`claude-agent-sdk`), with support for dual providers (Anthropic API / AWS Bedrock), external and in-process MCP server integration, Agent Skills, and a comprehensive test + eval framework.

The Python harness maintains feature parity with the TypeScript version while being idiomatically Python: Pydantic for validation, Click for CLI, pytest for testing, TOML for configuration, and `@tool` decorators for in-process MCP servers.

---

## Phase 1: Project Scaffolding & Core CLI (Week 1)

**Goal:** An installable Python package that accepts CLI args and runs an agent against the Anthropic API.

### 1.1 Project Setup (P0-8)
- [x] Create `pyproject.toml` with hatchling build backend, project metadata, dependencies, and tool config
- [x] Create `src/agent_harness/__init__.py` with package version
- [x] Create `src/agent_harness/__main__.py` — enables `python -m agent_harness`
- [x] Create `.env.example` with `ANTHROPIC_API_KEY`, `CLAUDE_CODE_USE_BEDROCK`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- [x] Create `.gitignore` — `__pycache__/`, `*.egg-info/`, `.env`, `dist/`, `evals/results/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`
- [x] Initialize git repository
- [x] Verify `pip install -e ".[dev]"` succeeds

### 1.2 Shared Types (P0-8)
- [x] Create `src/agent_harness/types.py`
  - `ToolName` literal type: `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebSearch`, `WebFetch`
  - Type aliases for provider configs, skill info, MCP server configs
  - All types use `from __future__ import annotations` for forward references

### 1.3 Config Loading & Validation (P0-4, P1-1)
- [x] Create `src/agent_harness/config.py`
  - `HarnessConfig` Pydantic model: `model`, `allowed_tools`, `skills_dir`, `mcp_servers`, `permission_mode`, `system_prompt`
  - `MCPServerConfig` Pydantic model: `command`, `args`, `env` with `${VAR}` interpolation
  - `load_config()` function: reads `harness.toml` if present, falls back to defaults
  - Environment variables override config file values
  - Default tools: `["Read", "Write", "Edit", "Bash", "Glob", "Grep"]`
  - Use stdlib `tomllib` (Python 3.11+) with `tomli` fallback for 3.10

### 1.4 CLI Entry Point (P0-1)
- [x] Create `src/agent_harness/cli.py`
  - Click command with options: `--prompt` (required), `--cwd`, `--output`, `--resume`, `--permission-mode`
  - Validate inputs, load config, resolve provider, discover skills, load MCP servers
  - Call agent execution and stream output to stdout
  - Exit code 0 on success, non-zero on failure
- [x] Wire up `pyproject.toml` `[project.scripts]` entry point: `agent-harness = "agent_harness.cli:main"`

### 1.5 Provider Resolution (P0-2)
- [x] Create `src/agent_harness/providers.py`
  - Detect provider from env: `CLAUDE_CODE_USE_BEDROCK=1` → Bedrock, else Anthropic
  - Validate required credentials for selected provider
  - `ANTHROPIC_API_KEY` for Anthropic; `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` for Bedrock
  - Return provider config dict/object for the Agent SDK
  - Clear error messages for missing credentials

### 1.6 Agent Initialization & Execution (P0-2)
- [x] Create `src/agent_harness/agent.py`
  - Initialize Agent SDK with resolved provider, tools, MCP servers, and skills
  - Execute `query()` with the user's prompt
  - `async for message in query()` — stream to stdout
  - Handle errors with user-friendly messages
  - Return result text, session ID, exit code
  - Support `--cwd` to scope file operations

---

## Phase 2: Bedrock, MCP Servers, In-Process Tools, Skills (Week 2)

**Goal:** Full provider parity, external and in-process MCP tool integration, and skill loading.

### 2.1 AWS Bedrock Provider (P0-3)
- [x] Extend `src/agent_harness/providers.py` with Bedrock provider construction
  - Validate Bedrock credentials at startup
  - Same agent behavior regardless of provider

### 2.2 External MCP Server Integration (P0-5)
- [x] Create `src/agent_harness/mcp.py`
  - Load MCP server declarations from `mcp-servers.json` (or `mcp_servers` section in `harness.toml`)
  - Validate each server has required `command` field
  - Support `${VAR_NAME}` interpolation in `env` blocks
  - Return parsed servers for Agent SDK consumption
- [x] Create `mcp-servers.json` with example configuration (e.g., Playwright, filesystem)

### 2.3 In-Process MCP Server (P0-6)
- [x] Create `src/agent_harness/tools_registry.py`
  - Example tools using `@tool` decorator: `lookup_user`, `run_query`
  - `create_custom_tools_server()` function using `create_sdk_mcp_server()`
  - Register in-process server alongside external servers in `ClaudeAgentOptions.mcp_servers`
  - Document how to add new in-process tools

### 2.4 Agent Skills Loading (P0-7)
- [x] Create `src/agent_harness/skills.py`
  - Scan configurable skills directory (default: `./.claude/skills/`)
  - Discover folders containing `SKILL.md` files
  - Read and return skill content for Agent SDK `setting_sources`
  - Log discovered skills at startup
- [x] Create `.claude/skills/example-skill/SKILL.md` with sample skill content

### 2.5 Wire Everything Together
- [x] Update `agent.py` to pass MCP servers (external + in-process), skills, and full config to `query()`
- [x] Update `cli.py` to orchestrate the complete flow
- [x] Verify end-to-end: `python -m agent_harness --prompt "List files"` works with tools and skills

---

## Phase 3: Unit Tests (Week 2-3)

**Goal:** Comprehensive unit test coverage for all non-agent-loop modules. No API keys needed.

### 3.1 Test Infrastructure (P0-9)
- [x] Configure pytest in `pyproject.toml` — `testpaths = ["tests"]`, `asyncio_mode = "auto"`, `timeout = 10`
- [x] Create `tests/__init__.py`
- [x] Verify `pytest tests/` runs and exits cleanly

### 3.2 Unit Test Files (P0-9)
- [x] `tests/test_config.py`
  - Valid TOML parsing into `HarnessConfig`
  - Missing optional fields use defaults
  - Environment variable overrides
  - Invalid/malformed config rejection with clear errors
  - `${VAR}` interpolation in MCP server env blocks

- [x] `tests/test_providers.py`
  - Anthropic selected when `ANTHROPIC_API_KEY` is set
  - Bedrock selected when `CLAUDE_CODE_USE_BEDROCK=1`
  - Clear error when no credentials are present
  - Correct model and region propagation

- [x] `tests/test_skills.py`
  - Discover skills from a populated directory
  - Handle empty skill directories
  - Ignore folders without `SKILL.md`
  - Report discovered skill names and paths

- [x] `tests/test_mcp.py`
  - Valid server declarations parsed correctly
  - Missing `command` field rejected
  - `${VAR}` interpolation resolves from environment
  - Empty/missing config file handled gracefully

- [x] `tests/test_cli.py`
  - `--prompt` is required
  - `--cwd` sets working directory
  - `--output json` enables JSON mode
  - `--resume` passes session ID
  - `--permission-mode` overrides config

### 3.3 Test Principles
- No network calls or API keys required
- All external dependencies mocked using `pytest-mock` / `unittest.mock`
- Target: 30+ tests, runs in under 10 seconds
- `mypy --strict` passes with zero errors

---

## Phase 4: Eval Framework (Week 3)

**Goal:** A structured eval system for testing agent behavior end-to-end with real API calls.

### 4.1 Eval Types & Helpers (P0-10)
- [x] Create `evals/helpers/__init__.py`
- [x] Create `evals/helpers/types.py`
  - `EvalTask`, `EvalResult`, `GradeResult`, `EvalGrader` dataclasses
  - Support for multi-trial runs and `pass@k` / `pass^k` metrics

- [x] Create `evals/helpers/run_agent.py`
  - `run_agent(prompt, working_dir, options)` — wraps SDK `query()`
  - Captures tool calls, response text, duration, exit code, errors
  - Returns `EvalResult` dataclass

- [x] Create `evals/helpers/graders.py`
  - `assert_output_contains(result, substring)` — case-insensitive
  - `assert_output_matches(result, pattern)` — regex match
  - `assert_tool_used(result, tool_name, count=None)`
  - `assert_tool_not_used(result, tool_name)`
  - `assert_file_exists(file_path)`
  - `assert_file_contains(file_path, substring)`
  - `assert_json_schema(result, pydantic_model)` — validate against Pydantic model
  - `assert_exit_code(result, code)`

- [x] Create `evals/helpers/model_grader.py`
  - `grade_with_model(result, rubric, model=None)` — sends output + rubric to Claude
  - Returns `GradeResult` with score (1–5) and explanation

- [x] Create `evals/helpers/reporter.py`
  - Writes JSON result files to `evals/results/`
  - Includes run_id, suite, provider, task results, summary

### 4.2 Eval Configuration (P0-10)
- [x] Create `evals/conftest.py`
  - Register custom markers: `eval`, `slow`
  - Auto-skip if `ANTHROPIC_API_KEY` not set
  - Default timeout: 120 seconds
  - Sequential execution (no parallel)

### 4.3 Eval Fixtures (P0-10)
- [x] Create `evals/fixtures/sample_project/` — `main.py`, `utils.py`, `README.md`
- [x] Create `evals/fixtures/sample_skill/SKILL.md` — skill that enforces a specific output format

### 4.4 Eval Suites (P0-10)
- [x] `evals/suites/test_built_in_tools.py` (3 tasks)
  - `test_file_listing_uses_glob` — list files, assert Glob tool used
  - `test_file_read_and_summarize` — read file, assert Read tool used and content present
  - `test_file_write_creates_file` — create file, assert file exists with content

- [x] `evals/suites/test_provider_parity.py` (2-3 tasks)
  - Parametrized tests running same prompt against Anthropic and Bedrock
  - Simple math task (no tools) and file analysis task (with tools)

- [x] `evals/suites/test_skills_loading.py` (2 tasks)
  - Verify skill influences agent behavior
  - Verify skill formatting instructions are followed

---

## Phase 5: P1 Features (Week 4)

**Goal:** Quality-of-life features for power users and CI integration.

### 5.1 Unified Configuration File (P1-1)
- [x] Finalize `harness.toml` schema — consolidates provider, tools, MCP, skills, permissions, subagents
- [x] Pydantic validation with clear error messages
- [x] Create example `harness.toml` with all sections documented via comments

### 5.2 Session Resumption (P1-2)
- [x] Add `--resume <session-id>` CLI flag
- [x] Print session ID at start of each run
- [x] Pass session ID to Agent SDK for context continuation

### 5.3 Subagent Definitions (P1-3)
- [x] Add `subagents` section to config schema
- [x] Each subagent: `name`, `description`, `prompt`, `tools`
- [x] Include example subagent (e.g., code-reviewer)

### 5.4 Permission Modes (P1-4)
- [x] Add `--permission-mode` CLI flag and config field
- [x] Support `bypassPermissions`, `acceptEdits`, `default`, `plan` modes
- [x] Default: `bypassPermissions` for automated use
- [x] Document security implications

### 5.5 Structured JSON Output (P1-5)
- [x] Implement `--output json` flag
- [x] Emit newline-delimited JSON events with `type`, `timestamp`, `payload`
- [x] Final event includes complete agent response

### 5.6 Hook System (P1-6)
- [x] Expose SDK hook system via `ClaudeAgentOptions.hooks`
- [x] Include example hooks: audit logger, dangerous-command blocker, read-only auto-approver
- [x] Document hook registration

---

## Phase 6: Documentation & Polish (Week 5)

- [ ] Write comprehensive README.md with quickstart, configuration reference, architecture overview
- [ ] Document all CLI flags, config options, and environment variables
- [ ] Document in-process MCP tool authoring with `@tool` decorator examples
- [ ] Document skill creation and directory conventions
- [ ] Add inline code comments for complex logic
- [ ] Run `mypy --strict` and fix all errors
- [ ] Run `ruff check` and `ruff format` and fix all issues
- [ ] Ensure all acceptance criteria from PRD are met
- [ ] Final pass on error messages and developer experience
- [ ] Create `CLAUDE.md` with project context (if decided — Open Question #5)

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI parser | `click` | More Pythonic than argparse, supports subcommands, PRD-specified |
| Config format | TOML (`harness.toml`) | stdlib `tomllib` in 3.11+, supports comments, standard for Python ecosystem |
| Config validation | Pydantic v2 | Best-in-class Python validation; replaces Zod from TypeScript version |
| Async runtime | anyio (via SDK) | SDK uses anyio internally; align rather than fight it |
| Test runner | pytest | De facto Python standard; parametrize maps to Vitest describe/it |
| Type checker | mypy --strict | Strictest type checking; PRD-specified |
| Linter/formatter | ruff | Fast, replaces flake8+isort+black; modern Python standard |
| In-process MCP | `@tool` + `create_sdk_mcp_server()` | Python-only SDK capability; key differentiator from TypeScript |
| Package layout | src layout (`src/agent_harness/`) | Prevents accidental imports; PEP 517 best practice |
| Python version | 3.10+ | `match` statements, `X | Y` union syntax, modern typing |
| Build backend | hatchling | Modern, fast, PEP 517 compliant |
| Package manager | pip (recommend `uv` for speed) | Universal compatibility; `uv` noted as faster alternative |
| MCP failure handling | Warn and skip | Resilient; don't block entire run for one server failure |
| Eval scheduling | Unit tests on every commit, evals nightly | Balance cost vs. coverage |
| Eval temp dirs | pytest `tmp_path` fixture | Auto-cleanup, no git pollution |
| License | MIT | PRD recommendation |

---

## Open Questions Resolution

| # | Question | Decision |
|---|----------|----------|
| 1 | Vertex AI in v1? | Defer to P2 |
| 2 | Minimum Python version? | 3.10+ (use `tomli` backport for <3.11) |
| 3 | YAML config support? | Defer; TOML only for v1 |
| 4 | MCP server startup failure handling? | Warn and skip; log the error |
| 5 | Include `CLAUDE.md`? | Yes, add in Phase 6 |
| 6 | License? | MIT |
| 7 | Eval CI cadence? | Unit tests every commit, evals nightly |
| 8 | Eval fixture temp dirs? | Use pytest `tmp_path` |
| 9 | CI pass rate threshold? | 100% pass@1 for `built-in-tools`, advisory for others |
| 10 | Use `uv` instead of pip? | Recommend `uv` in docs, support both |

---

## Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| `claude-agent-sdk` Python API instability | Pin to specific version, monitor changelog, wrap SDK calls in thin adapter |
| `@tool` decorator API changes | Isolate in `tools_registry.py`, easy to update |
| Bedrock model availability | Test early, document required AWS permissions and model access |
| MCP server startup latency | Add timeout configuration, parallel startup with anyio |
| Eval flakiness (LLM non-determinism) | Multi-trial support with pass@k metrics, generous grading criteria |
| Cost of running evals | Cost tier tagging, suite filtering, CI gates on unit tests only |
| Python 3.10 vs 3.11 `tomllib` | Use `tomli` backport with conditional import |

---

## File Structure (Final)

```
core-harness-python/
  src/
    agent_harness/
      __init__.py           # Package version
      __main__.py           # python -m agent_harness entry point
      cli.py                # Click-based CLI definition
      config.py             # Pydantic models + TOML config loading
      agent.py              # Agent SDK initialization & execution
      providers.py          # Provider detection (Anthropic vs Bedrock)
      skills.py             # Skill directory scanning & loading
      mcp.py                # MCP server config parsing
      tools_registry.py     # In-process MCP tool definitions (@tool)
      types.py              # Shared type aliases
  tests/
    __init__.py
    test_config.py
    test_providers.py
    test_skills.py
    test_mcp.py
    test_cli.py
  evals/
    conftest.py             # Eval-specific pytest config
    helpers/
      __init__.py
      run_agent.py          # Wraps SDK query() for evals
      graders.py            # Code-based grader utilities
      model_grader.py       # Model-based grader (Claude scoring)
      types.py              # EvalResult, GradeResult dataclasses
      reporter.py           # JSON result writer
    suites/
      test_built_in_tools.py
      test_provider_parity.py
      test_skills_loading.py
    fixtures/
      sample_project/
        main.py
        utils.py
        README.md
      sample_skill/
        SKILL.md
    results/                # Generated eval results (gitignored)
  .claude/
    skills/
      example-skill/
        SKILL.md
  harness.toml              # Unified configuration (TOML)
  mcp-servers.json          # MCP server declarations (external)
  pyproject.toml            # Project metadata, deps, tool config
  .env.example              # Environment variable template
  .gitignore
  README.md
  PLAN.md
  CLAUDE.md                 # Project context for Claude
```

---

## Mapping to TypeScript Harness

| TypeScript Module | Python Equivalent | Key Difference |
|-------------------|-------------------|----------------|
| `src/index.ts` (commander) | `src/agent_harness/cli.py` (Click) | Click decorators vs. commander chain |
| `src/config.ts` (Zod) | `src/agent_harness/config.py` (Pydantic) | TOML instead of JSON |
| `src/agent.ts` | `src/agent_harness/agent.py` | async for streaming, anyio runtime |
| `src/providers.ts` | `src/agent_harness/providers.py` | Same logic, Python types |
| `src/skills.ts` | `src/agent_harness/skills.py` | `pathlib.Path` instead of `fs` |
| `src/mcp.ts` | `src/agent_harness/mcp.py` | Same logic + in-process servers |
| — (no equivalent) | `src/agent_harness/tools_registry.py` | Python-only: `@tool` decorators |
| `src/types.ts` | `src/agent_harness/types.py` | Literal types, dataclasses |
| `vitest.config.ts` | `pyproject.toml [tool.pytest]` | Config in pyproject.toml |
| `evals/helpers/*.ts` | `evals/helpers/*.py` | Same architecture, pytest conventions |
| `evals/suites/*.eval.ts` | `evals/suites/test_*.py` | pytest classes instead of describe/it |
