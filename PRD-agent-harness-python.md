# PRD: Python Agent Harness — Reference Implementation

**Author:** Ajay Mehta
**Date:** March 3, 2026
**Status:** Draft
**Version:** 1.0
**Companion to:** [TypeScript Agent Harness PRD v1.1](./PRD-agent-harness.md)

---

## 1. Problem Statement

The TypeScript Agent Harness (v1.1) solved scaffolding pain for Node.js teams. But many teams building Claude-powered agents work primarily in Python — data science orgs, ML infrastructure teams, backend services written in Django/FastAPI, and DevOps groups scripting in Python. These teams face the same boilerplate burden (SDK wiring, provider switching, MCP server management, skill loading) with the added friction of translating TypeScript patterns into Python idioms.

The Python Agent SDK (`claude-agent-sdk`) provides a fully async API surface with `query()` and `ClaudeSDKClient`, native hook support, and in-process MCP servers via `@tool` decorators. A Python-native harness should exploit these capabilities — not just port the TypeScript version line-by-line.

**Who experiences this:** Python-first developers and teams building Claude-powered agents for data pipelines, research workflows, internal tooling, infrastructure automation, or API services.

**Cost of not solving it:** Same as the TypeScript harness — 1–2 days of scaffolding per project — compounded by the cognitive overhead of reverse-engineering TypeScript examples into Python patterns.

---

## 2. Goals

1. **Reduce time-to-first-agent to under 10 minutes.** Clone, `pip install`, configure an API key, run a working agent from the CLI.

2. **Provide an idiomatic Python foundation.** The harness should feel native: `pyproject.toml` for packaging, Pydantic for config validation, `asyncio`/`anyio` for concurrency, `click` for CLI, `pytest` for testing. No TypeScript-isms ported verbatim.

3. **Make provider switching trivial.** Swapping between Anthropic API and AWS Bedrock requires only an environment variable change.

4. **Demonstrate first-class MCP server integration** — both external (subprocess) servers declared in config and in-process Python servers using the SDK's `@tool` decorator and `create_sdk_mcp_server()`.

5. **Demonstrate Agent Skills integration.** Load and expose `SKILL.md` files from a local directory so the agent gains domain expertise through configuration, not code.

6. **Maintain feature parity with the TypeScript harness** for all P0 requirements, while taking advantage of Python-specific SDK capabilities (in-process MCP, async hooks, `anyio` runtime).

---

## 3. Non-Goals

- **Production deployment infrastructure.** This is a reference implementation and local development harness, not a production service with auth, rate limiting, or horizontal scaling.

- **GUI or web interface.** CLI-first. A FastAPI wrapper or Streamlit UI is out of scope for v1.

- **Multi-model support beyond Claude.** Targets Claude via the Anthropic Agent SDK only.

- **Custom tool implementation framework.** The harness uses built-in SDK tools and MCP servers. A generic tool-authoring framework is a separate effort.

- **TypeScript SDK support.** This is the Python counterpart. The TypeScript harness already exists.

---

## 4. User Stories

**As a Python developer starting a new agent project,** I want to clone a repo, run `pip install -e .`, and have a working agent in minutes so I can focus on agent logic rather than SDK wiring.

**As a developer building on AWS,** I want to switch from Anthropic API to Bedrock by setting `CLAUDE_CODE_USE_BEDROCK=1` so I can use my existing AWS credentials without code changes.

**As a developer integrating external tools,** I want to declare MCP servers in a JSON config so my agent can access databases, browsers, and APIs without writing integration code.

**As a Python developer building custom tools,** I want to define an in-process MCP server using `@tool` decorators so I can extend the agent with Python functions — no subprocess, no Node.js dependency.

**As a developer extending agent capabilities,** I want to drop a `SKILL.md` file into a skills directory so my agent gains new domain expertise without modifying harness code.

**As a developer testing agent behavior,** I want to run the agent from the CLI with a `--prompt` argument and get structured output so I can script tests and validate behavior in CI.

**As a developer working in a monorepo,** I want the harness to operate within a specific `--cwd` so file operations are scoped to a project folder.

**As a developer writing unit tests,** I want to run `pytest` and get fast, deterministic feedback on config loading, provider resolution, skill discovery, and CLI parsing — without needing an API key.

**As a developer validating agent behavior,** I want to run `pytest evals/` and see structured pass/fail results that tell me whether the agent correctly uses tools, follows skills, and produces expected outputs.

**As a developer adding a new eval,** I want to define a task with a prompt and a set of graders in a single Python file, drop it into `evals/suites/`, and have it discovered automatically by pytest.

**As a CI pipeline,** I want eval results written as JSON so I can gate deployments on pass rates and track agent quality over time.

---

## 5. Requirements

### Must-Have (P0)

**P0-1: CLI entry point with prompt argument**

The harness exposes a CLI command that accepts a prompt string and an optional working directory. The agent executes autonomously and streams output to stdout.

*Acceptance Criteria:*

- [ ] Running `python -m agent_harness --prompt "List all Python files"` executes the agent and prints results
- [ ] Running with `--cwd ./my-project` scopes file operations to that directory
- [ ] Exit code is 0 on success, non-zero on failure
- [ ] Agent output streams to stdout as it executes (not buffered until completion)
- [ ] `click` is used for CLI argument parsing

**P0-2: Anthropic API provider support**

The harness connects to Claude via the Anthropic API using an `ANTHROPIC_API_KEY` environment variable.

*Acceptance Criteria:*

- [ ] Setting `ANTHROPIC_API_KEY` and running the harness connects to Claude successfully
- [ ] The model used is `claude-opus-4-6` (or latest equivalent)
- [ ] Missing API key produces a clear error message at startup, not a runtime crash

**P0-3: AWS Bedrock provider support**

The harness connects to Claude on AWS Bedrock when configured via environment variables.

*Acceptance Criteria:*

- [ ] Setting `CLAUDE_CODE_USE_BEDROCK=1` plus standard AWS credentials connects to Bedrock
- [ ] The same prompt produces equivalent behavior regardless of provider
- [ ] Invalid or missing Bedrock credentials produce a clear error message

**P0-4: Built-in tool configuration**

The harness enables a configurable set of the SDK's built-in tools.

*Acceptance Criteria:*

- [ ] Configuration defines which tools are enabled via a Pydantic-validated config
- [ ] Default set includes: `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`
- [ ] Tools can be added or removed without modifying the agent loop code
- [ ] The agent successfully uses enabled tools during execution

**P0-5: MCP server integration (external)**

The harness loads external MCP server declarations from a configuration file and passes them to the Agent SDK.

*Acceptance Criteria:*

- [ ] A `mcp_servers` section in `harness.toml` (or standalone `mcp-servers.json`) declares MCP servers with `command` and `args`
- [ ] Declared MCP servers are available to the agent as tools during execution
- [ ] Adding a new MCP server requires only a config change, not code changes
- [ ] Example configuration includes at least one MCP server (e.g., filesystem)
- [ ] Invalid MCP server configuration produces a clear error at startup

**P0-6: In-process MCP server support**

The harness supports defining MCP tools in Python using the SDK's `@tool` decorator and `create_sdk_mcp_server()`.

*Acceptance Criteria:*

- [ ] An example in-process MCP server is included (e.g., a calculator or data-lookup tool)
- [ ] In-process servers are registered alongside external servers in `ClaudeAgentOptions.mcp_servers`
- [ ] Tools defined with `@tool` are callable by the agent during execution
- [ ] Documentation shows how to add new in-process tools

**P0-7: Agent Skills loading**

The harness discovers and loads Agent Skills from a local directory.

*Acceptance Criteria:*

- [ ] Skills are loaded from a configurable directory (default: `./.claude/skills/`)
- [ ] Each skill is a folder containing a `SKILL.md` file
- [ ] Loaded skills are passed to the agent via `ClaudeAgentOptions.setting_sources` or equivalent mechanism
- [ ] Adding a new skill requires only creating a folder with `SKILL.md` — no code changes
- [ ] The harness logs which skills were discovered at startup

**P0-8: Project structure and Python packaging**

The harness uses a modern, idiomatic Python project structure.

*Acceptance Criteria:*

- [ ] `pyproject.toml` for all project metadata, dependencies, and tool configuration (no `setup.py`, no `setup.cfg`)
- [ ] Source code in `src/agent_harness/` (src layout)
- [ ] Type hints throughout; passes `mypy --strict`
- [ ] Dependencies are minimal: `claude-agent-sdk`, `pydantic`, `click`, `python-dotenv`
- [ ] `pyproject.toml` defines scripts: `agent-harness` CLI entry point
- [ ] Python 3.10+ required (for `match` statements and modern typing)

**P0-9: Unit test suite**

The harness includes unit tests for all non-agent-loop modules using pytest. Tests run without API keys or network access.

*Acceptance Criteria:*

- [ ] Test runner is pytest, configured in `pyproject.toml` under `[tool.pytest.ini_options]`
- [ ] `pytest tests/` runs the full unit suite and exits with 0 on pass
- [ ] Config loading and validation (`config.py`) has tests covering: valid config parsing, missing required fields, environment variable overrides, malformed input rejection
- [ ] Provider resolver (`providers.py`) has tests covering: Anthropic selection when `ANTHROPIC_API_KEY` is set, Bedrock selection when `CLAUDE_CODE_USE_BEDROCK=1`, clear error when no credentials are present
- [ ] Skills loader (`skills.py`) has tests covering: discovering skills from a directory, handling empty skill directories, ignoring folders without `SKILL.md`, reporting discovered skills
- [ ] MCP config parser (`mcp.py`) has tests covering: valid server declarations, missing `command` field rejection, environment variable interpolation in `env` block
- [ ] CLI argument parsing (`cli.py`) has tests covering: `--prompt`, `--cwd`, `--output json`, `--resume`, missing required `--prompt`
- [ ] No unit test calls the Agent SDK or makes network requests — all external dependencies are mocked using `pytest-mock` or `unittest.mock`
- [ ] Tests run in under 10 seconds

**P0-10: LLM eval framework and structure**

The harness includes a structured eval framework for testing agent behavior end-to-end. Evals call the real Agent SDK (requiring API keys) and grade the agent's output and actions.

*Acceptance Criteria:*

- [ ] Eval files live in `evals/suites/` at the project root, separate from unit tests in `tests/`
- [ ] `pytest evals/` runs the eval suite; `pytest evals/suites/test_built_in_tools.py` runs a specific suite
- [ ] pytest is configured with a separate `conftest.py` in `evals/` (longer timeouts, sequential execution via `pytest-xdist` disabled, requires `ANTHROPIC_API_KEY`)
- [ ] The framework provides standard helper utilities (see Eval Helpers below)
- [ ] At least 3 example eval suites ship with the harness
- [ ] Each eval task is defined with: a natural-language prompt, a set of graders, an optional fixture directory, and metadata (suite name, tags, cost tier)
- [ ] Eval results are written to `evals/results/` as JSON
- [ ] The eval framework works identically regardless of provider

#### Eval Helpers (provided by `evals/helpers/`)

**`run_agent(prompt, options=None) -> EvalResult`** — Wraps the Agent SDK `query()` call, captures the full message stream, and returns a structured `EvalResult` dataclass.

**`assert_output_contains(result, substring)`** — Asserts the agent's final response contains the expected substring. Case-insensitive by default.

**`assert_output_matches(result, pattern)`** — Asserts the agent's final response matches a regex pattern.

**`assert_tool_used(result, tool_name, count=None)`** — Asserts the agent invoked a specific tool, optionally a specific number of times.

**`assert_tool_not_used(result, tool_name)`** — Asserts the agent did not invoke a specific tool.

**`assert_file_exists(file_path)`** — Asserts a file was created at the expected path.

**`assert_file_contains(file_path, substring)`** — Asserts a file exists and its content includes the expected substring.

**`assert_json_schema(result, schema)`** — Validates the agent's output against a Pydantic model.

**`assert_exit_code(result, code)`** — Asserts the agent exited with the expected code.

**`grade_with_model(result, rubric, model=None) -> GradeResult`** — Model-based grader. Sends the agent's output plus a rubric to Claude for scoring. Returns a score (1–5) and explanation. Used only when code-based graders cannot capture the quality dimension.

#### Eval Task Definition Format

```python
from dataclasses import dataclass, field
from typing import Callable, Awaitable

@dataclass
class EvalTask:
    name: str                                    # e.g. "file-listing-basic"
    suite: str                                   # e.g. "built-in-tools"
    tags: list[str]                              # e.g. ["smoke", "fast"]
    prompt: str                                  # The prompt sent to the agent
    graders: list["EvalGrader"]                  # All must pass
    working_dir: str | None = None               # Optional fixture directory
    options: dict | None = None                  # Tool overrides, MCP servers, etc.
    timeout: float = 60.0                        # Max execution time in seconds
    trials: int = 1                              # Number of times to run
    cost_tier: str = "low"                       # "low" | "medium" | "high"

@dataclass
class EvalGrader:
    name: str                                    # e.g. "lists-ts-files"
    type: str                                    # "code" | "model"
    fn: Callable[["EvalResult"], Awaitable["GradeResult"]]

@dataclass
class EvalResult:
    response_text: str
    tool_calls: list[dict]                       # [{name, input, output}, ...]
    duration_seconds: float
    exit_code: int
    errors: list[str] = field(default_factory=list)

@dataclass
class GradeResult:
    passed: bool
    score: float | None = None                   # 0–1 for code, 1–5 for model
    reason: str = ""
```

#### Included Eval Suites

**Suite: `built-in-tools`** (3–5 tasks, low cost)
Validates that the agent correctly uses built-in SDK tools.

- *file-listing*: Prompt asks agent to list files in a fixture directory. Graders assert the agent used `Glob` or `Bash`, and the output contains expected filenames.
- *file-read*: Prompt asks agent to read and summarize a specific file. Graders assert `Read` tool was used and output contains key content.
- *file-write*: Prompt asks agent to create a file with specific content. Graders assert the file exists and contains the expected content.

**Suite: `provider-parity`** (2–3 tasks, medium cost)
Runs the same tasks against both Anthropic API and Bedrock to verify equivalent behavior. Uses `pytest.mark.parametrize` — same prompt and graders, different provider config.

**Suite: `skills-loading`** (2 tasks, low cost)
Validates that loaded skills influence agent behavior. Includes a fixture skill that instructs the agent to always respond in a specific format. Grader asserts the output follows that format.

#### Eval Results Format

Each run writes a JSON file to `evals/results/`:

```json
{
  "run_id": "2026-03-03T14-30-00Z",
  "suite": "built-in-tools",
  "provider": "anthropic",
  "tasks": [
    {
      "name": "file-listing",
      "trials": [
        {
          "passed": true,
          "duration_seconds": 4.2,
          "graders": [
            { "name": "used-glob-tool", "passed": true, "reason": "Glob called 1 time" },
            { "name": "output-contains-files", "passed": true, "reason": "Found 'main.py' in output" }
          ],
          "tool_calls": ["Glob", "Read"],
          "token_usage": { "input": 1200, "output": 340 }
        }
      ],
      "pass_rate": 1.0
    }
  ],
  "summary": { "total": 3, "passed": 3, "failed": 0, "pass_rate": 1.0 }
}
```

#### Multi-Trial and Non-Determinism

Because LLM outputs are non-deterministic, evals support running multiple trials per task. The framework reports **pass@k** (at least one trial passed) and **pass^k** (all trials passed). For CI gating, the default policy is pass@1. Teams can adjust this per suite.

### Nice-to-Have (P1)

**P1-1: Unified configuration file (`harness.toml`)**

A single TOML config that consolidates provider settings, tool selection, MCP server declarations, and skill directory paths. TOML is chosen over JSON for Python projects because it supports comments, is the standard for `pyproject.toml`, and is stdlib-supported via `tomllib` (Python 3.11+).

*Acceptance Criteria:*

- [ ] One config file controls all harness behavior
- [ ] Config is validated at startup with Pydantic, with clear error messages for invalid entries
- [ ] Environment variables can override config file values (env takes precedence)

**P1-2: Session resumption**

The harness supports resuming a previous agent session by passing a session ID.

*Acceptance Criteria:*

- [ ] Running with `--resume <session-id>` continues a previous session with full context
- [ ] Session IDs are printed at the start of each run

**P1-3: Subagent definitions**

The harness supports declaring named subagents with specialized prompts and tool sets.

*Acceptance Criteria:*

- [ ] Subagents are declared in `harness.toml` with `description`, `prompt`, and `tools`
- [ ] The main agent can delegate to subagents using the Task tool
- [ ] At least one example subagent is included (e.g., a code-reviewer)

**P1-4: Permission modes**

The harness supports configurable permission modes.

*Acceptance Criteria:*

- [ ] Permission mode is set via config or CLI flag (`--permission-mode`)
- [ ] Default is `bypassPermissions` for automated/CI use
- [ ] Documentation explains the security implications of each mode

**P1-5: Structured JSON output mode**

*Acceptance Criteria:*

- [ ] Running with `--output json` emits newline-delimited JSON events
- [ ] Each event includes `type`, `timestamp`, and relevant payload
- [ ] Final result event includes the agent's complete response text

**P1-6: Hook system for lifecycle events**

The harness exposes the SDK's hook system through configuration.

*Acceptance Criteria:*

- [ ] Hooks can be defined as Python functions and registered via `ClaudeAgentOptions.hooks`
- [ ] Example hooks are included: audit logger, dangerous-command blocker, read-only auto-approver
- [ ] Hooks are documented with clear examples

### Future Considerations (P2)

**P2-1: Plugin support.** Support loading Agent SDK plugins that bundle skills, MCP servers, and slash commands. Reserve a `plugins` field in the config schema.

**P2-2: Multi-turn interactive mode.** Support a REPL-like mode where the user can have a back-and-forth conversation using `ClaudeSDKClient`.

**P2-3: Telemetry and cost tracking.** Track token usage, tool invocations, and execution time per run. Emit a summary at the end of each execution.

**P2-4: Google Vertex AI provider.** Add Vertex as a third provider option.

**P2-5: FastAPI wrapper.** Expose the agent as an HTTP endpoint for service-oriented architectures.

---

## 6. Success Metrics

### Leading Indicators (within 2 weeks of release)

| Metric | Target | Stretch | Measurement |
|--------|--------|---------|-------------|
| Time from clone to first successful agent run | < 10 min | < 5 min | Manual testing with fresh developer |
| Harness runs with zero config on Anthropic API | 100% | — | CI test on every commit |
| Bedrock provider passes same test suite as Anthropic API | 100% | — | CI test matrix |
| MCP server (external + in-process) loads and agent uses its tools | 100% for included examples | — | Integration test |
| Skills directory is scanned and skills are available to agent | 100% | — | Integration test |
| Unit test suite passes with 100% of modules covered | 100% | >90% line coverage | `pytest tests/` in CI |
| All 3 included eval suites pass on Anthropic API | pass@1 for all tasks | pass^3 | `pytest evals/` |
| New eval can be added by creating a single file (no framework changes) | Yes | — | Manual validation |
| `mypy --strict` passes with zero errors | 100% | — | CI check |

### Lagging Indicators (within 3 months)

| Metric | Target | Stretch | Measurement |
|--------|--------|---------|-------------|
| Internal teams using harness as starting point for new agent projects | 3+ | 5+ | Survey / repo forks |
| Time saved per project vs. building from scratch | 1+ days | 2+ days | Developer interviews |
| Community contributions (PRs, skills, MCP configs, in-process tools) | 5+ | 15+ | GitHub activity |

---

## 7. Architecture Overview

### Project Structure

```
core-harness-python/
  src/
    agent_harness/
      __init__.py
      __main__.py          # python -m agent_harness entry point
      cli.py               # Click-based CLI definition
      config.py            # Pydantic models + config loading
      agent.py             # Agent initialization & execution
      providers.py         # Provider detection (Anthropic vs Bedrock)
      skills.py            # Skill directory scanning & loading
      mcp.py               # MCP server config parsing
      tools_registry.py    # In-process MCP tool definitions
      types.py             # Shared type aliases
  tests/
    __init__.py
    test_config.py
    test_providers.py
    test_skills.py
    test_mcp.py
    test_cli.py
  evals/
    conftest.py            # Eval-specific pytest config (timeouts, API key check)
    helpers/
      __init__.py
      run_agent.py         # Wraps SDK query() for eval context
      graders.py           # Code-based grader utilities
      model_grader.py      # Model-based grader (secondary)
      types.py             # EvalResult, GradeResult dataclasses
      reporter.py          # JSON result writer
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
    results/               # Generated eval results (gitignored)
  .claude/
    skills/
      example-skill/
        SKILL.md
  harness.toml             # Unified configuration (P1)
  mcp-servers.json         # MCP server declarations (P0 fallback)
  pyproject.toml           # Project metadata, deps, tool config
  .env.example             # Environment variable template
  README.md
```

### Data Flow

```
CLI args + .env + harness.toml
        │
        ▼
  Config Loader (Pydantic validation)
        │
        ▼
  Provider Resolver (Anthropic / Bedrock)
        │
        ▼
  MCP Server Loader
    ├── External servers (from mcp-servers.json)
    └── In-process servers (from tools_registry.py)
        │
        ▼
  Skills Loader (scan .claude/skills/**/SKILL.md)
        │
        ▼
  ClaudeAgentOptions assembled
        │
        ▼
  Agent SDK query() call
    - allowed_tools: [configured built-in tools]
    - mcp_servers: {external + in-process}
    - setting_sources: ["project"]
    - permission_mode: from config
        │
        ▼
  async for message in query():
    stream to stdout
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Config format | TOML (`harness.toml`) | stdlib `tomllib` in 3.11+, supports comments, standard for Python ecosystem |
| Config validation | Pydantic v2 | Best-in-class Python validation; replaces Zod |
| CLI framework | Click | More Pythonic than argparse, supports subcommands for future expansion |
| Async runtime | anyio (via SDK) | SDK uses anyio internally; align with it rather than fight it |
| Test runner | pytest | De facto standard for Python; parametrize replaces Vitest's `describe`/`it` naturally |
| In-process MCP | `@tool` + `create_sdk_mcp_server()` | Python-only capability; no TypeScript equivalent |
| Package layout | src layout (`src/agent_harness/`) | Prevents accidental imports of uninstalled code; PEP 517 best practice |

---

## 8. Key Differences from TypeScript Harness

| Aspect | TypeScript Harness | Python Harness |
|--------|-------------------|----------------|
| Package manager | npm / package.json | pip / pyproject.toml |
| Config validation | Zod | Pydantic v2 |
| CLI parsing | commander / yargs | Click |
| Test runner | Vitest | pytest |
| Type checking | TypeScript compiler | mypy --strict |
| Module resolution | Node16 / ES2022 | Standard Python imports |
| MCP servers | External only (subprocess) | External + in-process (`@tool` decorator) |
| Async runtime | Native JS async/await | anyio (via SDK) |
| Config file | harness.config.json | harness.toml |
| Entry point | `npx ts-node src/index.ts` | `python -m agent_harness` or `agent-harness` CLI |
| Build step | `tsc` → `dist/` | None (interpreted); optional `build` for wheel |

---

## 9. Open Questions

| # | Question | Owner | Blocking? |
|---|----------|-------|-----------|
| 1 | Should the harness support Google Vertex AI as a third provider in v1, or defer to P2? | Ajay / Eng | Non-blocking (default: defer) |
| 2 | What is the minimum Python version to target? Recommendation: 3.10 (for `match` and modern `|` union types). 3.11+ if we want stdlib `tomllib`. | Eng | Blocking |
| 3 | Should `harness.toml` be the sole config, or also support `harness.yaml` for teams that prefer YAML? | Eng | Non-blocking |
| 4 | How should the harness handle MCP server startup failures — skip with warning, or fail the entire run? | Eng | Non-blocking |
| 5 | Should the harness include a `CLAUDE.md` memory file with project context by default? | Ajay | Non-blocking |
| 6 | What license? (Recommendation: MIT) | Ajay / Legal | Blocking |
| 7 | Should evals run in CI on every commit or only nightly/manual? (Recommendation: unit tests on every commit, evals nightly) | Eng | Non-blocking |
| 8 | Should eval fixtures that write files use `tmp_path` (pytest built-in) or a custom temp directory? (Recommendation: `tmp_path`) | Eng | Non-blocking |
| 9 | What pass rate threshold gates CI deployment? (Recommendation: 100% pass@1 for `built-in-tools`, advisory for others) | Ajay / Eng | Non-blocking |
| 10 | Should the harness use `uv` as the recommended package manager instead of pip? `uv` is significantly faster and becoming the standard for modern Python projects. | Eng | Non-blocking |

---

## 10. Timeline Considerations

- **No hard deadlines.** Internal accelerator, not a contractual commitment.
- **Dependency:** `claude-agent-sdk` Python package must be at a stable release. As of March 2026, the SDK is actively maintained.
- **Suggested phasing:**
  - **Week 1:** P0 items — CLI, Anthropic provider, built-in tools, project structure. pytest setup and unit tests for config + CLI modules.
  - **Week 2:** P0 items — Bedrock provider, external MCP server integration, in-process MCP tools, Agent Skills loading. Unit tests for providers, skills, MCP modules.
  - **Week 3:** P0 items — Eval framework helpers, types, and reporter. Ship the 3 included eval suites. CI integration. mypy strict pass.
  - **Week 4:** P1 items — unified `harness.toml` config, session resumption, subagents, hooks. Expand eval coverage.
  - **Week 5:** Documentation, example skills, example MCP configs, example in-process tools, README.

---

## Appendix A: Example Usage

```bash
# Basic usage with Anthropic API
export ANTHROPIC_API_KEY=sk-ant-...
python -m agent_harness --prompt "Find all TODO comments in this codebase and summarize them"

# Or using the installed CLI entry point
agent-harness --prompt "Find all TODO comments in this codebase and summarize them"

# With AWS Bedrock
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION=us-east-1
agent-harness --prompt "Review the authentication module for security issues"

# Scoped to a specific directory
agent-harness --prompt "Refactor utils.py" --cwd ./my-project

# With JSON output for CI
agent-harness --prompt "Run the test suite and fix failures" --output json

# Resume a previous session
agent-harness --prompt "Continue where we left off" --resume abc123-session-id
```

## Appendix B: Example MCP Server Configuration

**External servers (`mcp-servers.json`):**

```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"]
  },
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
    }
  }
}
```

**In-process server (`src/agent_harness/tools_registry.py`):**

```python
from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any


@tool("lookup_user", "Look up a user by email", {"email": str})
async def lookup_user(args: dict[str, Any]) -> dict[str, Any]:
    # Replace with actual lookup logic
    email = args["email"]
    return {
        "content": [{"type": "text", "text": f"User {email}: active, role=admin"}]
    }


@tool("run_query", "Execute a read-only SQL query", {"sql": str})
async def run_query(args: dict[str, Any]) -> dict[str, Any]:
    sql = args["sql"]
    # Replace with actual database query
    return {
        "content": [{"type": "text", "text": f"Query result for: {sql}"}]
    }


def create_custom_tools_server():
    """Create the in-process MCP server with all custom tools."""
    return create_sdk_mcp_server(
        name="custom-tools",
        version="1.0.0",
        tools=[lookup_user, run_query],
    )
```

## Appendix C: Example Skill Structure

```
.claude/skills/
  code-reviewer/
    SKILL.md        # Instructions for code review behavior
  security-auditor/
    SKILL.md        # Instructions for security-focused analysis
  api-designer/
    SKILL.md        # Instructions for REST API design review
```

Each `SKILL.md` contains natural-language instructions that the agent incorporates into its system context when the skill is loaded.

## Appendix D: Key Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| `claude-agent-sdk` | Agent SDK core | Latest |
| `pydantic` | Config validation | ^2.x |
| `click` | CLI argument parsing | ^8.x |
| `python-dotenv` | Environment variable loading | ^1.x |
| `anyio` | Async runtime (SDK dependency) | ^4.x |
| `pytest` | Test runner | ^8.x |
| `pytest-asyncio` | Async test support | ^0.24+ |
| `pytest-mock` | Mocking utilities | ^3.x |
| `mypy` | Static type checking | ^1.x |

## Appendix E: pytest Configuration

**In `pyproject.toml`:**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
timeout = 10

[tool.mypy]
strict = true
python_version = "3.10"
```

**Eval-specific `evals/conftest.py`:**

```python
import os
import pytest

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "eval: mark test as an LLM eval")
    config.addinivalue_line("markers", "slow: mark test as slow-running")

@pytest.fixture(autouse=True)
def require_api_key():
    """Skip eval tests if no API key is set."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY required for evals")

@pytest.fixture
def eval_timeout():
    """Default timeout for eval tasks: 120 seconds."""
    return 120.0
```

## Appendix F: Example Eval File

```python
# evals/suites/test_built_in_tools.py

import pytest
from evals.helpers.run_agent import run_agent
from evals.helpers.graders import (
    assert_tool_used,
    assert_output_contains,
    assert_file_contains,
)


@pytest.mark.eval
class TestBuiltInTools:

    @pytest.mark.asyncio
    async def test_file_listing_uses_glob(self):
        """Agent uses Glob to list files in a directory."""
        result = await run_agent(
            prompt="List all Python files in this directory",
            working_dir="./evals/fixtures/sample_project",
            options={"allowed_tools": ["Glob", "Read", "Bash"]},
        )

        assert_tool_used(result, "Glob")
        assert_output_contains(result, "main.py")
        assert_output_contains(result, "utils.py")

    @pytest.mark.asyncio
    async def test_file_read_and_summarize(self):
        """Agent reads a file and reports its contents."""
        result = await run_agent(
            prompt="Read utils.py and tell me what functions it defines",
            working_dir="./evals/fixtures/sample_project",
            options={"allowed_tools": ["Read", "Glob"]},
        )

        assert_tool_used(result, "Read")
        assert_output_contains(result, "format_date")

    @pytest.mark.asyncio
    async def test_file_write_creates_file(self, tmp_path):
        """Agent creates a file with specified content."""
        result = await run_agent(
            prompt='Create a file called hello.txt containing "Hello, world!"',
            working_dir=str(tmp_path),
            options={"allowed_tools": ["Write"]},
        )

        assert_tool_used(result, "Write")
        assert_file_contains(tmp_path / "hello.txt", "Hello, world!")
```

## Appendix G: Example `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agent-harness"
version = "0.1.0"
description = "Reference implementation for building Claude-powered agents in Python"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [{ name = "Ajay Mehta" }]
dependencies = [
    "claude-agent-sdk",
    "pydantic>=2.0",
    "click>=8.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-mock>=3.0",
    "pytest-timeout>=2.0",
    "mypy>=1.0",
    "ruff>=0.4",
]

[project.scripts]
agent-harness = "agent_harness.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
timeout = 10

[tool.mypy]
strict = true
python_version = "3.10"

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
```

## Appendix H: Pydantic Config Model

```python
# src/agent_harness/config.py

from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class MCPServerConfig(BaseModel):
    """Configuration for an external MCP server."""
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

    @field_validator("env", mode="before")
    @classmethod
    def interpolate_env_vars(cls, v: dict[str, str]) -> dict[str, str]:
        """Replace ${VAR} patterns with actual environment variable values."""
        resolved = {}
        for key, val in v.items():
            if val.startswith("${") and val.endswith("}"):
                env_name = val[2:-1]
                resolved[key] = os.environ.get(env_name, "")
            else:
                resolved[key] = val
        return resolved


class HarnessConfig(BaseModel):
    """Top-level harness configuration."""
    model: str = "claude-opus-4-6"
    allowed_tools: list[str] = Field(
        default=["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
    )
    skills_dir: Path = Path(".claude/skills")
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    permission_mode: str = "bypassPermissions"
    system_prompt: str | None = None

    @field_validator("permission_mode")
    @classmethod
    def validate_permission_mode(cls, v: str) -> str:
        valid = {"default", "acceptEdits", "plan", "bypassPermissions"}
        if v not in valid:
            raise ValueError(f"permission_mode must be one of {valid}, got '{v}'")
        return v


def load_config(config_path: Path | None = None) -> HarnessConfig:
    """Load config from TOML file, with env var overrides."""
    ...
```
