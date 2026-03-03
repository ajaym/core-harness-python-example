# PRD: TypeScript Agent Harness — Reference Implementation

**Author:** Ajay Mehta
**Date:** March 2, 2026
**Status:** Draft
**Version:** 1.1 (added unit testing + eval framework requirements)

---

## 1. Problem Statement

Building AI agents with Claude requires integrating multiple moving parts: the Anthropic Agent SDK, model provider configuration (Anthropic API vs. AWS Bedrock), MCP server connections for external tooling, and Agent Skills for specialized capabilities. Today, each new agent project starts from scratch, wiring together boilerplate for SDK initialization, provider switching, skill loading, and MCP server management. This slows down prototyping, introduces inconsistencies across projects, and creates a barrier for teams who want to experiment with agent-driven workflows.

**Who experiences this:** Developers and teams building Claude-powered agents for internal tools, CI/CD automation, code review, research workflows, or customer-facing products.

**Cost of not solving it:** Every new agent project burns 1-2 days on scaffolding before the team can focus on the actual agent logic. Configuration drift between projects leads to bugs when porting capabilities. Teams without deep SDK knowledge avoid building agents entirely.

---

## 2. Goals

1. **Reduce time-to-first-agent to under 10 minutes.** A developer should be able to clone the harness, configure a provider, and run a working agent from the CLI within a single sitting.

2. **Provide a single, extensible foundation for diverse agent use cases.** The same harness should serve as the starting point for a code-review agent, a research agent, a file-processing agent, or a custom workflow — without forking.

3. **Make provider switching trivial.** Swapping between Anthropic API and AWS Bedrock should require only an environment variable change, not code changes.

4. **Demonstrate first-class MCP server integration.** The harness should show how to declare, connect, and use MCP servers, making external tool integration a configuration concern rather than a coding task.

5. **Demonstrate Agent Skills integration.** The harness should load and expose Agent Skills from a local directory, showing how specialized capabilities are discovered and used by the agent.

---

## 3. Non-Goals

- **Production deployment infrastructure.** This is a reference implementation and local development harness, not a production-ready service with auth, rate limiting, or horizontal scaling. (Separate initiative.)

- **GUI or web interface.** The harness is CLI-first. A web UI or chat interface is out of scope for v1. (Premature — let the CLI prove the architecture first.)

- **Multi-model support beyond Claude.** The harness targets Claude Opus via the Anthropic Agent SDK only. Supporting OpenAI, Gemini, or other models is out of scope. (Different SDK, different patterns.)

- **Custom tool implementation framework.** The harness uses the SDK's built-in tools and MCP servers. Building a framework for defining net-new custom tools is a separate effort.

- **Python SDK support.** This reference implementation is TypeScript-only. A Python equivalent may follow but is a separate project.

---

## 4. User Stories

**As a developer starting a new agent project,** I want to clone a repository and run a working agent in minutes so that I can focus on the agent's purpose rather than SDK wiring.

**As a developer building on AWS,** I want to switch from Anthropic API to Bedrock by changing an environment variable so that I can use my existing AWS credentials and stay within my organization's cloud boundaries.

**As a developer integrating external tools,** I want to declare MCP servers in a configuration file so that my agent can access databases, browsers, APIs, and file systems without writing integration code.

**As a developer extending agent capabilities,** I want to drop a SKILL.md file into a skills directory so that my agent gains new domain expertise without modifying the core harness code.

**As a developer testing agent behavior,** I want to run the agent from the CLI with a prompt argument and see structured output so that I can script tests and validate agent behavior in CI.

**As a developer working in a monorepo,** I want the harness to operate within a specific working directory so that the agent's file operations are scoped to the project folder, not the entire filesystem.

**As a developer writing unit tests,** I want to run `npm test` and get fast, deterministic feedback on whether the harness's config loading, provider resolution, skill discovery, and CLI parsing work correctly — without needing an API key.

**As a developer validating agent behavior,** I want to run `npm run test:eval` and see structured pass/fail results that tell me whether the agent correctly uses tools, follows skills, and produces expected outputs, so that I can catch regressions before they reach users.

**As a developer adding a new eval,** I want to define a task with a prompt and a set of graders in a single TypeScript file, drop it into the `evals/` directory, and have it picked up automatically — without modifying framework code.

**As a CI pipeline,** I want eval results written as JSON so that I can parse them, gate deployments on pass rates, and track agent quality over time.

**As a team lead evaluating agent patterns,** I want to read the harness code and understand the architecture in under 30 minutes so that I can decide whether to adopt it for my team's projects.

---

## 5. Requirements

### Must-Have (P0)

**P0-1: CLI entry point with prompt argument**
The harness exposes a CLI command that accepts a prompt string and an optional working directory. The agent executes autonomously and streams output to stdout.

*Acceptance Criteria:*
- [ ] Running `npx ts-node src/index.ts --prompt "List all TypeScript files"` executes the agent and prints results
- [ ] Running with `--cwd ./my-project` scopes file operations to that directory
- [ ] Exit code is 0 on success, non-zero on failure
- [ ] Agent output streams to stdout as it executes (not buffered until completion)

**P0-2: Anthropic API provider support**
The harness connects to Claude Opus via the Anthropic API using an `ANTHROPIC_API_KEY` environment variable.

*Acceptance Criteria:*
- [ ] Setting `ANTHROPIC_API_KEY` and running the harness connects to Claude successfully
- [ ] The model used is the latest Claude Opus (claude-opus-4-6 or equivalent latest)
- [ ] Missing API key produces a clear error message at startup, not a runtime crash

**P0-3: AWS Bedrock provider support**
The harness connects to Claude Opus on AWS Bedrock when configured via environment variables.

*Acceptance Criteria:*
- [ ] Setting `CLAUDE_CODE_USE_BEDROCK=1` plus standard AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION) connects to Bedrock
- [ ] The same prompt produces equivalent behavior regardless of provider
- [ ] Invalid or missing Bedrock credentials produce a clear error message

**P0-4: Built-in tool configuration**
The harness enables a configurable set of the SDK's built-in tools (Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch).

*Acceptance Criteria:*
- [ ] A configuration file or constant defines which tools are enabled
- [ ] The default set includes: Read, Write, Edit, Bash, Glob, Grep
- [ ] Tools can be added or removed without modifying the agent loop code
- [ ] The agent successfully uses enabled tools during execution

**P0-5: MCP server integration**
The harness loads MCP server declarations from a configuration file and passes them to the Agent SDK.

*Acceptance Criteria:*
- [ ] A `mcp-servers.json` (or section in a unified config) declares MCP servers with `command` and `args`
- [ ] Declared MCP servers are available to the agent as tools during execution
- [ ] Adding a new MCP server requires only a config change, not code changes
- [ ] Example configuration includes at least one MCP server (e.g., Playwright or filesystem)
- [ ] Invalid MCP server configuration produces a clear error at startup

**P0-6: Agent Skills loading**
The harness discovers and loads Agent Skills from a local directory.

*Acceptance Criteria:*
- [ ] Skills are loaded from a configurable directory (default: `./.claude/skills/`)
- [ ] Each skill is a folder containing a `SKILL.md` file
- [ ] Loaded skills are passed to the agent via the SDK's `settingSources` or equivalent mechanism
- [ ] Adding a new skill requires only creating a folder with SKILL.md — no code changes
- [ ] The harness logs which skills were discovered at startup

**P0-7: Project structure and TypeScript configuration**
The harness uses a clean, conventional TypeScript project structure.

*Acceptance Criteria:*
- [ ] TypeScript with strict mode enabled
- [ ] `tsconfig.json` targets ES2022 with Node16 module resolution
- [ ] Source code in `src/`, build output in `dist/`
- [ ] `package.json` includes `build`, `start`, `dev`, `test`, and `test:eval` scripts
- [ ] Dependencies are minimal: `@anthropic-ai/claude-agent-sdk`, `typescript`, `zod` (for config validation), and `dotenv`

**P0-8: Unit test suite**
The harness includes unit tests for all non-agent-loop modules using Vitest. These tests run without API keys or network access and validate the harness's own logic.

*Acceptance Criteria:*
- [ ] Test runner is Vitest, configured in `vitest.config.ts`
- [ ] `npm test` runs the full unit suite and exits with 0 on pass, non-zero on failure
- [ ] Config loading and validation (`config.ts`) has tests covering: valid config parsing, missing required fields, environment variable overrides, malformed JSON rejection
- [ ] Provider resolver (`providers.ts`) has tests covering: Anthropic selection when `ANTHROPIC_API_KEY` is set, Bedrock selection when `CLAUDE_CODE_USE_BEDROCK=1`, clear error when no credentials are present
- [ ] Skills loader (`skills.ts`) has tests covering: discovering skills from a directory, handling empty skill directories, ignoring folders without SKILL.md, reporting discovered skills
- [ ] MCP config parser (`mcp.ts`) has tests covering: valid server declarations, missing `command` field rejection, environment variable interpolation in `env` block
- [ ] CLI argument parsing (`index.ts` or `cli.ts`) has tests covering: `--prompt`, `--cwd`, `--output json`, `--resume`, missing required `--prompt`
- [ ] No unit test calls the Agent SDK or makes network requests — all external dependencies are mocked
- [ ] Tests run in under 10 seconds on a standard machine

**P0-9: LLM eval framework and structure**
The harness includes a structured eval framework for testing agent behavior end-to-end. Evals call the real Agent SDK (requiring API keys) and grade the agent's output and actions against defined criteria. The framework follows Anthropic's eval best practices: tasks, trials, graders, and eval suites.

*Acceptance Criteria:*
- [ ] Eval files live in `evals/` at the project root, separate from unit tests in `src/`
- [ ] `npm run test:eval` runs the eval suite; `npm run test:eval -- --suite <name>` runs a specific suite
- [ ] Vitest is used as the runner, with a separate `vitest.config.evals.ts` config (longer timeouts, sequential by default, requires `ANTHROPIC_API_KEY`)
- [ ] The framework provides standard helper utilities (see Eval Helpers below)
- [ ] At least 3 example evals ship with the harness (see Included Eval Suites below)
- [ ] Each eval task is defined with: a natural-language prompt, a set of graders (assertions), an expected environment state (optional), and metadata (suite name, tags, estimated cost tier)
- [ ] Eval results are written to `evals/results/` as JSON with timestamp, task name, pass/fail, grader details, and execution duration
- [ ] The eval framework works identically regardless of provider (Anthropic API or Bedrock)

#### Eval Helpers (provided by `evals/helpers/`)

The framework provides these reusable utilities so eval authors write tasks, not infrastructure:

**`runAgent(prompt, options?)`** — Wraps the Agent SDK `query()` call, captures the full message stream, and returns a structured `EvalResult` containing: the final text response, the list of tool calls made (name, input, output), total execution time, and any errors.

**`assertOutputContains(result, substring)`** — Code-based grader. Asserts the agent's final response contains the expected substring. Case-insensitive by default.

**`assertOutputMatches(result, regex)`** — Code-based grader. Asserts the agent's final response matches a regular expression.

**`assertToolUsed(result, toolName, count?)`** — Code-based grader. Asserts the agent invoked a specific tool, optionally a specific number of times.

**`assertToolNotUsed(result, toolName)`** — Code-based grader. Asserts the agent did not invoke a specific tool (negative test).

**`assertFileExists(filePath)`** — Code-based grader. Asserts a file was created at the expected path in the working directory.

**`assertFileContains(filePath, substring)`** — Code-based grader. Asserts a file exists and its content includes the expected substring.

**`assertJsonSchema(result, schema)`** — Code-based grader. Validates the agent's output against a Zod schema (useful when `--output json` is used).

**`assertExitCode(result, code)`** — Code-based grader. Asserts the agent exited with the expected code.

**`gradeWithModel(result, rubric, options?)`** — Model-based grader (secondary pattern). Sends the agent's output plus a rubric to Claude for scoring. Returns a score (1-5) and explanation. Used only when code-based graders cannot capture the quality dimension. Options include model selection and temperature.

#### Eval Task Definition Format

Each eval task is a TypeScript object following this structure:

```typescript
interface EvalTask {
  name: string;                    // Unique identifier, e.g. "file-listing-basic"
  suite: string;                   // Eval suite name, e.g. "built-in-tools"
  tags: string[];                  // For filtering, e.g. ["smoke", "fast", "read-only"]
  prompt: string;                  // The prompt sent to the agent
  workingDir?: string;             // Optional fixture directory for the eval
  options?: AgentOptions;          // Tool overrides, MCP servers, skills, etc.
  graders: EvalGrader[];           // One or more graders (all must pass)
  timeout?: number;                // Max execution time in ms (default: 60_000)
  trials?: number;                 // Number of times to run (default: 1)
  costTier?: "low" | "medium" | "high"; // Estimated API cost per trial
}

interface EvalGrader {
  name: string;                    // Descriptive name, e.g. "lists-ts-files"
  type: "code" | "model";         // Grading approach
  fn: (result: EvalResult) => Promise<GradeResult>; // The grading function
}

interface GradeResult {
  pass: boolean;
  score?: number;                  // 0-1 for code graders, 1-5 for model graders
  reason: string;                  // Human-readable explanation
}
```

#### Included Eval Suites

The harness ships with these example eval suites to validate core functionality and serve as templates:

**Suite: `built-in-tools`** (3-5 tasks, low cost)
Validates that the agent correctly uses built-in SDK tools.

- *file-listing*: Prompt asks agent to list files in a fixture directory. Graders assert the agent used `Glob` or `Bash(ls)`, and the output contains expected filenames.
- *file-read*: Prompt asks agent to read and summarize a specific file. Graders assert `Read` tool was used and output contains key content from the file.
- *file-write*: Prompt asks agent to create a file with specific content. Graders assert the file exists and contains the expected content.

**Suite: `provider-parity`** (2-3 tasks, medium cost)
Runs the same tasks against both Anthropic API and Bedrock to verify equivalent behavior. Uses parameterized tests — same prompt and graders, different provider config.

**Suite: `skills-loading`** (2 tasks, low cost)
Validates that loaded skills influence agent behavior. Includes a fixture skill that instructs the agent to always respond in a specific format. Grader asserts the output follows that format.

#### Eval Results Format

Each run writes a JSON file to `evals/results/`:

```json
{
  "runId": "2026-03-02T14-30-00Z",
  "suite": "built-in-tools",
  "provider": "anthropic",
  "tasks": [
    {
      "name": "file-listing",
      "trials": [
        {
          "pass": true,
          "durationMs": 4200,
          "graders": [
            { "name": "used-glob-tool", "pass": true, "reason": "Glob called 1 time" },
            { "name": "output-contains-files", "pass": true, "reason": "Found 'index.ts' in output" }
          ],
          "toolCalls": ["Glob", "Read"],
          "tokenUsage": { "input": 1200, "output": 340 }
        }
      ],
      "passRate": 1.0
    }
  ],
  "summary": { "total": 3, "passed": 3, "failed": 0, "passRate": 1.0 }
}
```

#### Multi-Trial and Non-Determinism

Because LLM outputs are non-deterministic, evals support running multiple trials per task. The framework reports **pass@k** (at least one trial passed) and **pass^k** (all trials passed) following Anthropic's recommended metrics. For CI gating, the default policy is pass@1 (a single trial must pass). Teams can adjust this threshold per suite.

### Nice-to-Have (P1)

**P1-1: Unified configuration file**
A single `harness.config.json` (or `.ts`) that consolidates provider settings, tool selection, MCP server declarations, and skill directory paths.

*Acceptance Criteria:*
- [ ] One config file controls all harness behavior
- [ ] Config is validated at startup with clear error messages for invalid entries
- [ ] Environment variables can override config file values (env takes precedence)

**P1-2: Session resumption**
The harness supports resuming a previous agent session by passing a session ID.

*Acceptance Criteria:*
- [ ] Running with `--resume <session-id>` continues a previous session with full context
- [ ] Session IDs are printed at the start of each run

**P1-3: Subagent definitions**
The harness supports declaring named subagents with specialized prompts and tool sets.

*Acceptance Criteria:*
- [ ] Subagents are declared in the config file with `description`, `prompt`, and `tools`
- [ ] The main agent can delegate to subagents using the Task tool
- [ ] At least one example subagent is included (e.g., a code-reviewer)

**P1-4: Permission modes**
The harness supports configurable permission modes (e.g., `bypassPermissions`, `acceptEdits`).

*Acceptance Criteria:*
- [ ] Permission mode is set via config or CLI flag
- [ ] Default is `bypassPermissions` for automated/CI use
- [ ] Documentation explains the security implications of each mode

**P1-5: Structured JSON output mode**
The harness supports outputting results as structured JSON for programmatic consumption.

*Acceptance Criteria:*
- [ ] Running with `--output json` emits newline-delimited JSON events
- [ ] Each event includes `type`, `timestamp`, and relevant payload
- [ ] Final result event includes the agent's complete response text

### Future Considerations (P2)

**P2-1: Hook system for lifecycle events.**
Allow users to define PreToolUse / PostToolUse hooks in the config to audit, log, or gate tool usage. Design the config structure now to accommodate this later.

**P2-2: Plugin support.**
Support loading Agent SDK plugins that bundle skills, MCP servers, and slash commands together. Ensure the config schema has a `plugins` field reserved.

**P2-3: Multi-turn interactive mode.**
Support a REPL-like mode where the user can have a back-and-forth conversation with the agent, not just single-prompt execution.

**P2-4: Telemetry and cost tracking.**
Track token usage, tool invocations, and execution time per run. Emit a summary at the end of each execution.

---

## 6. Success Metrics

### Leading Indicators (within 2 weeks of release)

| Metric | Target | Stretch | Measurement |
|--------|--------|---------|-------------|
| Time from clone to first successful agent run | < 10 min | < 5 min | Manual testing with fresh developer |
| Harness compiles and runs with zero config on Anthropic API | 100% | — | CI test on every commit |
| Bedrock provider passes same test suite as Anthropic API | 100% | — | CI test matrix |
| MCP server loads and agent uses its tools | 100% for included examples | — | Integration test |
| Skills directory is scanned and skills are available to agent | 100% | — | Integration test |
| Unit test suite passes with 100% of modules covered | 100% | >90% line coverage | `npm test` in CI |
| All 3 included eval suites pass on Anthropic API | pass@1 for all tasks | pass^3 | `npm run test:eval` |
| New eval can be added by creating a single file (no framework changes) | Yes | — | Manual validation |

### Lagging Indicators (within 3 months)

| Metric | Target | Stretch | Measurement |
|--------|--------|---------|-------------|
| Internal teams using harness as starting point for new agent projects | 3+ | 5+ | Survey / repo forks |
| Time saved per project vs. building from scratch | 1+ days | 2+ days | Developer interviews |
| Community contributions (PRs, skills, MCP configs) | 5+ | 15+ | GitHub activity |

---

## 7. Architecture Overview

```
core-harness/
  src/
    index.ts            # CLI entry point, arg parsing
    config.ts           # Config loading & validation (Zod schemas)
    agent.ts            # Agent initialization & execution
    providers.ts        # Provider detection (Anthropic vs Bedrock)
    skills.ts           # Skill directory scanning & loading
    mcp.ts              # MCP server config parsing
    types.ts            # Shared TypeScript types
    __tests__/          # Unit tests (co-located with source)
      config.test.ts
      providers.test.ts
      skills.test.ts
      mcp.test.ts
      cli.test.ts
  evals/
    helpers/
      run-agent.ts      # Wraps SDK query() for eval context
      graders.ts        # Code-based grader utilities
      model-grader.ts   # Model-based grader (secondary)
      types.ts          # EvalTask, EvalResult, GradeResult types
      reporter.ts       # JSON result writer
    suites/
      built-in-tools.eval.ts
      provider-parity.eval.ts
      skills-loading.eval.ts
    fixtures/            # Static test data for evals
      sample-project/
        index.ts
        utils.ts
        README.md
      sample-skill/
        SKILL.md
    results/             # Generated eval results (gitignored)
  .claude/
    skills/             # Agent Skills directory (SKILL.md files)
      example-skill/
        SKILL.md
  mcp-servers.json      # MCP server declarations
  harness.config.json   # Unified configuration (P1)
  vitest.config.ts      # Unit test config
  vitest.config.evals.ts # Eval config (longer timeouts, sequential)
  package.json
  tsconfig.json
  .env.example          # Environment variable template
  README.md
```

### Data Flow

```
CLI args + .env + config
        |
        v
  Config Loader (Zod validation)
        |
        v
  Provider Resolver (Anthropic / Bedrock)
        |
        v
  Agent SDK query() call
    - allowedTools: [configured built-in tools]
    - mcpServers: {loaded from mcp-servers.json}
    - settingSources: ['project']  (loads .claude/skills/)
        |
        v
  Stream messages to stdout
```

---

## 8. Open Questions

| # | Question | Owner | Blocking? |
|---|----------|-------|-----------|
| 1 | Should the harness support Google Vertex AI as a third provider in v1, or defer to P2? | Ajay / Eng | Non-blocking (default: defer) |
| 2 | What is the minimum Node.js version to target? (Recommendation: Node 20 LTS) | Eng | Blocking |
| 3 | Should the config file be JSON or TypeScript? TypeScript configs allow comments and type checking but add complexity. | Eng | Non-blocking |
| 4 | How should the harness handle MCP server startup failures — skip the server with a warning, or fail the entire run? | Eng | Non-blocking |
| 5 | Should the harness include a `CLAUDE.md` memory file with project context by default? | Ajay | Non-blocking |
| 6 | What license should the reference implementation use? (Recommendation: MIT) | Ajay / Legal | Blocking |
| 7 | Should evals run in CI on every commit (expensive) or only on a nightly/manual schedule? (Recommendation: unit tests on every commit, evals nightly or on-demand) | Eng | Non-blocking |
| 8 | Should eval fixtures that write files use a temp directory that auto-cleans, or write to the fixture dir and rely on git-clean? (Recommendation: temp directory via `vitest`'s `beforeEach`) | Eng | Non-blocking |
| 9 | What pass rate threshold should gate a CI deployment? (Recommendation: 100% pass@1 for the `built-in-tools` suite, advisory-only for others) | Ajay / Eng | Non-blocking |

---

## 9. Timeline Considerations

- **No hard deadlines.** This is an internal accelerator, not a contractual commitment.
- **Dependency:** The `@anthropic-ai/claude-agent-sdk` TypeScript package must be at a stable release. As of March 2026, the SDK is actively maintained with a public changelog.
- **Suggested phasing:**
  - **Week 1:** P0 items — CLI, Anthropic provider, built-in tools, project structure. Vitest setup and unit tests for config + CLI modules.
  - **Week 2:** P0 items — Bedrock provider, MCP server integration, Agent Skills loading. Unit tests for providers, skills, MCP modules.
  - **Week 3:** P0 items — Eval framework helpers, types, and reporter. Ship the 3 included eval suites. CI integration.
  - **Week 4:** P1 items — unified config, session resumption, subagents. Expand eval coverage.
  - **Week 5:** Documentation, example skills, example MCP configs, README

---

## Appendix A: Example Usage

```bash
# Basic usage with Anthropic API
export ANTHROPIC_API_KEY=sk-ant-...
npx ts-node src/index.ts --prompt "Find all TODO comments in this codebase and summarize them"

# With AWS Bedrock
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION=us-east-1
npx ts-node src/index.ts --prompt "Review the authentication module for security issues"

# Scoped to a specific directory
npx ts-node src/index.ts --prompt "Refactor utils.ts" --cwd ./my-project

# With JSON output for CI
npx ts-node src/index.ts --prompt "Run the test suite and fix failures" --output json
```

## Appendix B: Example MCP Server Configuration

```json
{
  "playwright": {
    "command": "npx",
    "args": ["@playwright/mcp@latest"]
  },
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
| `@anthropic-ai/claude-agent-sdk` | Agent SDK core | Latest |
| `typescript` | Language | ^5.x |
| `zod` | Config validation | ^3.25+ |
| `dotenv` | Environment variable loading | ^16.x |
| `commander` or `yargs` | CLI argument parsing | Latest |
| `vitest` | Test runner (unit + evals) | ^3.x |

## Appendix E: Vitest Configuration Examples

**Unit tests (`vitest.config.ts`):**
```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["src/**/*.test.ts"],
    environment: "node",
    testTimeout: 10_000,
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      exclude: ["src/**/*.test.ts", "src/types.ts"],
    },
  },
});
```

**Evals (`vitest.config.evals.ts`):**
```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["evals/suites/**/*.eval.ts"],
    environment: "node",
    testTimeout: 120_000,        // 2 min per task — agent calls are slow
    sequence: { concurrent: false }, // Sequential by default to control cost
    retry: 0,                     // No retries — use trials instead
    setupFiles: ["evals/helpers/setup.ts"], // Validates API key present
  },
});
```

## Appendix F: Example Eval File

```typescript
// evals/suites/built-in-tools.eval.ts
import { describe, it, expect } from "vitest";
import { runAgent } from "../helpers/run-agent";
import { assertToolUsed, assertOutputContains } from "../helpers/graders";

describe("built-in-tools", () => {
  it("file-listing: agent uses Glob to list files", async () => {
    const result = await runAgent({
      prompt: "List all TypeScript files in this directory",
      workingDir: "./evals/fixtures/sample-project",
      options: { allowedTools: ["Glob", "Read", "Bash"] },
    });

    assertToolUsed(result, "Glob");
    assertOutputContains(result, "index.ts");
    assertOutputContains(result, "utils.ts");
  });

  it("file-read: agent reads and summarizes a file", async () => {
    const result = await runAgent({
      prompt: "Read utils.ts and tell me what functions it exports",
      workingDir: "./evals/fixtures/sample-project",
      options: { allowedTools: ["Read", "Glob"] },
    });

    assertToolUsed(result, "Read");
    assertOutputContains(result, "formatDate");
  });

  it("file-write: agent creates a file with specified content", async () => {
    const result = await runAgent({
      prompt: 'Create a file called hello.txt containing "Hello, world!"',
      workingDir: "./evals/fixtures/sample-project",
      options: { allowedTools: ["Write"] },
    });

    assertToolUsed(result, "Write");
    // assertFileContains checks the filesystem
    assertFileContains(
      "./evals/fixtures/sample-project/hello.txt",
      "Hello, world!"
    );
  });
});
```
