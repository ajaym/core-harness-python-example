# Python Agent Harness — Reference Implementation

A CLI-driven foundation for building Claude-powered agents using the Python Agent SDK. Clone it, `pip install`, configure an API key, and have a working agent in under 10 minutes.

## What This Is

This harness eliminates the boilerplate of wiring together the Claude Agent SDK, provider configuration, MCP servers, and Agent Skills in Python. It provides:

- **Dual provider support** — Anthropic API or AWS Bedrock, switchable via environment variable
- **MCP server integration** — Declare external tool servers in config, no code changes needed
- **In-process MCP tools** — Define Python tools with `@tool` decorators, no subprocess or Node.js needed
- **Agent Skills** — Drop a `SKILL.md` into a directory and the agent gains new capabilities
- **Built-in tool management** — Configure which SDK tools (Read, Write, Edit, Bash, Glob, Grep) are available
- **Subagent definitions** — Declare specialized subagents in config with custom prompts and tools
- **Session resumption** — Resume previous agent sessions by ID
- **Structured JSON output** — Machine-readable newline-delimited JSON for CI pipelines
- **Unit tests + eval framework** — pytest-based testing with structured LLM evals for agent behavior validation

## Quickstart

```bash
# Clone and install
git clone <repo-url>
cd core-harness-python-example
pip install -e ".[dev]"

# Configure provider
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY or Bedrock credentials

# Run an agent
python -m agent_harness --prompt "List all Python files in this directory"

# Or use the installed CLI entry point
agent-harness --prompt "List all Python files in this directory"

# Run with a specific working directory
agent-harness --prompt "Summarize README.md" --cwd ./my-project

# JSON output for CI
agent-harness --prompt "Analyze this codebase" --output json

# Resume a previous session
agent-harness --prompt "Continue where we left off" --resume <session-id>

# Run tests
pytest tests/           # Unit tests (no API key needed)
pytest evals/           # LLM evals (requires ANTHROPIC_API_KEY)
```

## CLI Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--prompt <text>` | Yes | — | The prompt to send to the agent |
| `--cwd <directory>` | No | Current directory | Working directory for agent file operations |
| `--output <format>` | No | `text` | Output format: `text` or `json` |
| `--resume <session-id>` | No | — | Resume a previous session by ID |
| `--permission-mode <mode>` | No | Config value | Permission mode: `default`, `acceptEdits`, `bypassPermissions` |

## Architecture

```
CLI args + .env + harness.toml
        │
        v
  Config Loader (Pydantic validation)
        │
        v
  Provider Resolver (Anthropic / Bedrock)
        │
        v
  MCP Server Loader
    ├── External servers (from mcp-servers.json)
    └── In-process servers (from tools_registry.py)
        │
        v
  Skills Loader (scan .claude/skills/**/SKILL.md)
        │
        v
  ClaudeAgentOptions assembled
        │
        v
  Agent SDK query()
    - allowed_tools: [configured built-in tools]
    - mcp_servers: {external + in-process}
    - setting_sources: ["project"]
    - permission_mode: from config
        │
        v
  async for message in query():
    stream to stdout
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `src/agent_harness/cli.py` | Click-based CLI entry point |
| `src/agent_harness/config.py` | Pydantic config models + TOML loading |
| `src/agent_harness/agent.py` | Agent SDK initialization and execution |
| `src/agent_harness/providers.py` | Provider detection (Anthropic vs Bedrock) |
| `src/agent_harness/skills.py` | Skill directory scanning and loading |
| `src/agent_harness/mcp.py` | MCP server config parsing |
| `src/agent_harness/tools_registry.py` | In-process MCP tools via `@tool` decorator |
| `src/agent_harness/types.py` | Shared type aliases |

## Configuration

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API authentication |
| `CLAUDE_CODE_USE_BEDROCK` | Set to `1` to use AWS Bedrock |
| `AWS_ACCESS_KEY_ID` | AWS credentials (Bedrock) |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials (Bedrock) |
| `AWS_REGION` | AWS region (Bedrock) |

### Unified Config (`harness.toml`)

```toml
# Model to use for the agent
model = "claude-opus-4-6"

# Built-in SDK tools to enable
allowed_tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]

# Directory containing Agent Skills
skills_dir = ".claude/skills"

# Permission mode for agent operations
permission_mode = "bypassPermissions"

# External MCP server declarations
[mcp_servers.playwright]
command = "npx"
args = ["@playwright/mcp@latest"]

[mcp_servers.github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env = { GITHUB_PERSONAL_ACCESS_TOKEN = "${GITHUB_TOKEN}" }

# Subagent definitions
[subagents.code-reviewer]
description = "Reviews code for bugs, style issues, and best practices"
prompt = "You are a code reviewer. Analyze the provided code."
tools = ["Read", "Glob", "Grep"]
```

Environment variables in `env` blocks are interpolated at startup using `${VAR_NAME}` syntax.

### MCP Servers (`mcp-servers.json`)

Alternative to `[mcp_servers]` in `harness.toml` — declare external tool servers:

```json
{
  "playwright": {
    "command": "npx",
    "args": ["@playwright/mcp@latest"]
  },
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"]
  }
}
```

### In-Process MCP Tools

Define Python tools that the agent can call directly — no subprocess needed:

```python
# src/agent_harness/tools_registry.py
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("lookup_user", "Look up a user by email", {"email": str})
async def lookup_user(args: dict[str, Any]) -> dict[str, Any]:
    email = args["email"]
    return {"content": [{"type": "text", "text": f"User {email}: active"}]}

def create_custom_tools_server():
    return create_sdk_mcp_server(
        name="custom-tools",
        version="1.0.0",
        tools=[lookup_user],
    )
```

### Agent Skills (`.claude/skills/`)

Add domain expertise by creating skill folders with a `SKILL.md`:

```
.claude/skills/
  code-reviewer/
    SKILL.md        # Instructions for code review behavior
  security-auditor/
    SKILL.md        # Instructions for security-focused analysis
```

Each `SKILL.md` contains natural-language instructions that the agent incorporates into its context.

## Testing

### Unit Tests

```bash
pytest tests/           # 30+ tests, runs in <10 seconds
```

Covers config loading, provider resolution, skill discovery, MCP parsing, and CLI args. No API keys or network calls needed. All external dependencies are mocked.

### LLM Evals

```bash
pytest evals/           # Requires ANTHROPIC_API_KEY
pytest evals/suites/test_built_in_tools.py   # Run a specific suite
```

7+ end-to-end agent behavior tests across 3 suites:

| Suite | Tests | Description |
|-------|-------|-------------|
| `built-in-tools` | 3 | Validates file listing, reading, and writing |
| `provider-parity` | 2-3 | Verifies consistent behavior across Anthropic and Bedrock |
| `skills-loading` | 2 | Confirms skills influence agent behavior |

Eval results are written as JSON to `evals/results/` for CI integration.

## Type Checking & Linting

```bash
mypy src/               # Static type checking (strict mode)
ruff check src/ tests/  # Linting
ruff format src/ tests/ # Formatting
```

## Project Structure

```
core-harness-python/
  src/agent_harness/       # Main package
  tests/                   # Unit tests (pytest, no API key)
  evals/                   # LLM evals (pytest, requires API key)
    helpers/               # Eval utilities (graders, runner, reporter)
    suites/                # Eval test suites
    fixtures/              # Test fixture files
    results/               # Generated results (gitignored)
  .claude/skills/          # Agent Skills directory
  harness.toml             # Unified configuration
  mcp-servers.json         # External MCP server declarations
  pyproject.toml           # Package metadata and tool config
  .env.example             # Environment variable template
```

## Requirements

- Python 3.10+
- `claude-agent-sdk` (latest)
- `pydantic` >= 2.0
- `click` >= 8.0
- `python-dotenv` >= 1.0

## Differences from TypeScript Harness

| Aspect | TypeScript | Python |
|--------|-----------|--------|
| Package manager | npm | pip / uv |
| Config validation | Zod | Pydantic v2 |
| CLI parsing | commander | Click |
| Test runner | Vitest | pytest |
| Type checking | TypeScript compiler | mypy --strict |
| Config format | JSON | TOML |
| MCP servers | External only | External + in-process (`@tool`) |
| Entry point | `npx tsx src/index.ts` | `python -m agent_harness` |

## License

MIT
