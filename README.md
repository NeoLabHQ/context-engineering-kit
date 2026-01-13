<picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/CEK-header.png">
    <img src="docs/assets/CEK-header.png" alt="Context Engineering Kit - advanced context engineering techniques" />
</picture>

<div align="center">

[![License](https://img.shields.io/badge/license-GPL%203.0-blue.svg)](LICENSE)
[![agentskills.io](https://img.shields.io/badge/format-agentskills.io-purple.svg)](https://agentskills.io)
[![Mentioned in Awesome Claude Code](https://awesome.re/mentioned-badge.svg)](https://github.com/hesreallyhim/awesome-claude-code)

[Install](#quick-start) · [Plugins](#plugins-list) · [Github Action](#usage-in-github-actions) · [Docs](https://cek.neolab.finance/)

</div>

# [Context Engineering Kit](https://cek.neolab.finance)

Hand-crafted collection of advanced context engineering techniques and patterns with minimal token footprint, focused on improving agent result quality and predictability.

Marketplace is based on prompts used daily by our company developers for a long time, while adding plugins from benchmarked papers and high-quality projects.

## Supported Agents

Universal support based on <agentskills.io> and [openskills](https://github.com/numman-ali/openskills) standards.

| Agent | How it works | Status |
|:------|:-------------|:------:|
| **Claude Code** | Native plugin system | ✅ Native |
| **Cursor** | openskills → AGENTS.md | ✅ Universal |
| **Windsurf** | openskills → AGENTS.md | ✅ Universal |
| **Cline** | openskills → AGENTS.md | ✅ Universal |
| **OpenCode** | Native skill support | ✅ Native |
| **Amp Code** | openskills → AGENTS.md | ✅ Universal |

## Key Features

- **Simple to Use** - Easy to install and use without any dependencies. Contains automatically used skills and self-explanatory commands.
- **Token-Efficient** - Carefully crafted prompts and architecture, preferring commands with sub-agents over skills when possible, to minimize populating context with unnecessary information.
- **Quality-Focused** - Each plugin is focused on meaningfully improving agent results in a specific area.
- **Granular** - Install only the plugins you need. Each plugin loads only its specific agents, commands, and skills. Each without overlap and redundant skills.
- **Scientifically proven** - Plugins are based on proven techniques and patterns that were tested by well-trusted benchmarks and studies.

## Quick Start

### Step 1: Install Marketplaces and Plugin

#### Claude Code

Open Claude Code and add the Context Engineering Kit marketplace

```bash
/plugin marketplace add NeoLabHQ/context-engineering-kit
```

This makes all plugins available for installation, but does not load any agents or skills into your context.

Install any plugins, for example reflexion

```bash
/plugin install reflexion@NeoLabHQ/context-engineering-kit
```

Each installed plugin loads only its specific agents, commands, and skills into Claude's context.

#### Cursor, Windsurf, Cline, OpenCode

Commands installation is available for Cursor and OpenCode:

<details>
<summary>Cursor</summary>

```bash
curl -fsSL https://raw.githubusercontent.com/NeoLabHQ/context-engineering-kit/main/.bin/install-commands.sh | bash
```

</details>

<details>
<summary>OpenCode</summary>

```bash
curl -fsSL https://raw.githubusercontent.com/NeoLabHQ/context-engineering-kit/main/.bin/install-commands.sh | bash -s -- --agent opencode
```

</details>

Use [OpenSkills](https://github.com/numman-ali/openskills) to install skills for broad range of agents:

```bash
npx openskills install NeoLabHQ/context-engineering-kit
npx openskills sync
```

### Step 2: Use Plugin

```bash
> claude "implement user authentication"
# Claude implements user authentication, then you can ask it to reflect on implementation

> /reflexion:reflect
# It analyses results and suggests improvements
# If issues are obvious, it will fix them immediately
# If they are minor, it will suggest improvements that you can respond to
> fix the issues

# If you would like it to avoid issues that were found during reflection to appear again,
# ask claude to extract resolution strategies and save the insights to project memory
> /reflexion:memorize
```

Alternatively, you can use the `reflect` word in intial prompt:

```bash
> claude "implement user authentication, then reflect"
# Claude implements user authentication,
# then hook automatically runs /reflexion:reflect
```

In order to use this hook, need to have `bun` installed. But for overral command in not required.

## Documentation

You can find the complete Context Engineering Kit documentation [here](https://cek.neolab.finance).

## Plugins List

To view all available plugins:

```bash
/plugin
```

- [Reflexion](https://cek.neolab.finance/plugins/reflexion) - Introduces feedback and refinement loops to improve output quality.
- [Code Review](https://cek.neolab.finance/plugins/code-review) - Introduces codebase and PR review commands and skills using multiple specialized agents.
- [Git](https://cek.neolab.finance/plugins/git) - Introduces commands for commit and PRs creation.
- [Test-Driven Development](https://cek.neolab.finance/plugins/tdd) - Introduces commands for test-driven development, common anti-patterns and skills for testing using subagents.
- [Subagent-Driven Development](https://cek.neolab.finance/plugins/sadd) - Introduces skills for subagent-driven development, dispatches fresh subagent for each task with code review between tasks, enabling fast iteration with quality gates.
- [Domain-Driven Development](https://cek.neolab.finance/plugins/ddd) - Introduces commands to update CLAUDE.md with best practices for domain-driven development, focused on code quality, and includes Clean Architecture, SOLID principles, and other design patterns.
- [Spec-Driven Development](https://cek.neolab.finance/plugins/sdd) - Introduces commands for specification-driven development, based on Github Spec Kit, OpenSpec and BMad Method. Uses specialized agents for effective context management and quality review.
- [FPF - First Principles Framework](https://cek.neolab.finance/plugins/fpf) - Introduces structured reasoning using ADI cycle (Abduction-Deduction-Induction) with knowledge layer progression. Uses workflow command pattern with fpf-agent for hypothesis generation, verification, and auditable decision-making.
- [Kaizen](https://cek.neolab.finance/plugins/kaizen) - Inspired by Japanese continuous improvement philosophy, Agile and Lean development practices. Introduces commands for analysis of root causes of issues and problems, including 5 Whys, Cause and Effect Analysis, and other techniques.
- [Customaize Agent](https://cek.neolab.finance/plugins/customaize-agent) - Commands and skills for writing and refining commands, hooks, and skills for Claude Code. Includes Anthropic Best Practices and [Agent Persuasion Principles](https://arxiv.org/abs/2508.00614) that can be useful for sub-agent workflows.
- [Docs](https://cek.neolab.finance/plugins/docs) - Commands for analyzing projects, writing and refining documentation.
- [Tech Stack](https://cek.neolab.finance/plugins/tech-stack) - Commands for setting up or updating CLAUDE.md file with best practices for specific languages or frameworks.
- [MCP](https://cek.neolab.finance/plugins/mcp) - Commands for setting up well-known MCP server integration if needed and updating CLAUDE.md file with requirements to use this MCP server for the current project.

### Reflexion

Collection of commands that force the LLM to reflect on previous response and output. Includes **automatic reflection hooks** that trigger when you include "reflect" in your prompt.

**How to install**

```bash
/plugin install reflexion@NeoLabHQ/context-engineering-kit
```

**Commands**

- `/reflexion:reflect` - Reflect on previous response and output, based on Self-refinement framework for iterative improvement with complexity triage and verification
- `/reflexion:memorize` - Memorize insights from reflections and update the CLAUDE.md file with this knowledge. Curates insights from reflections and critiques into CLAUDE.md using Agentic Context Engineering
- `/reflexion:critique` - Comprehensive multi-perspective review using specialized judges with debate and consensus building

**Hooks**

- **Automatic Reflection Hook** - Triggers `/reflexion:reflect` automatically when "reflect" appears in your prompt

#### Theoretical Foundation

Based on papers like [Self-Refine](https://arxiv.org/abs/2303.17651) and [Reflexion](https://arxiv.org/abs/2303.11366). These techniques improve the output of large language models by introducing feedback and refinement loops.

They are proven to **increase output quality by 8–21%** based on both automatic metrics and human preferences across seven diverse tasks, including dialogue generation, coding, and mathematical reasoning, when compared to standard one-step model outputs.

Full list of included patterns and techniques:

- [Self-Refinement / Iterative Refinement](https://arxiv.org/abs/2303.17651) - One model generates, then reviews and improves its own output
- [Constitutional AI (CAI) / RLAIF](https://arxiv.org/abs/2212.08073) - One model generates responses, another critiques them based on principles
- [Critic-Generator or Verifier-Generator Architecture](https://arxiv.org/abs/2510.14660v1) - Generator model creates outputs, Critic/verifier model evaluates and provides feedback
- [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) - One LLM evaluates/scores outputs from another LLM
- [Debate / Multi-Agent Debate](https://arxiv.org/abs/2305.14325) - Multiple models propose and critique solutions
- [Generate-Verify-Refine (GVR)](https://arxiv.org/abs/2204.05511) - Three-stage process: generate → verify → refine based on verification

On top of that, the plugin is based on the [Agentic Context Engineering](https://arxiv.org/abs/2510.04618) paper that uses memory updates after reflection, and **consistently outperforms strong baselines by 10.6%** on agents.

Also includes the following techniques:

- [Chain-of-Verification (CoVe)](https://arxiv.org/abs/2309.11495) - Model generates answer, then verification questions, then revises
- [Tree of Thoughts (ToT)](https://arxiv.org/abs/2305.10601) - Explores multiple reasoning paths with evaluation
- [Process Reward Models (PRM)](https://arxiv.org/abs/2305.20050) - Evaluates reasoning steps rather than just final answers

### Code Review

Comprehensive code review commands using multiple specialized agents for thorough code quality evaluation.

**How to install**

```bash
/plugin install code-review@NeoLabHQ/context-engineering-kit
```

**Commands**

- `/code-review:review-local-changes` - Comprehensive review of local uncommitted changes using specialized agents with code improvement suggestions
- `/code-review:review-pr` - Comprehensive pull request review using specialized agents

**Agents**

This plugin uses multiple specialized agents for comprehensive code quality analysis:

- **bug-hunter** - Identifies potential bugs, edge cases, and error-prone patterns
- **code-quality-reviewer** - Evaluates code structure, readability, and maintainability
- **contracts-reviewer** - Reviews interfaces, API contracts, and data models
- **historical-context-reviewer** - Analyzes changes in relation to codebase history and patterns
- **security-auditor** - Identifies security vulnerabilities and potential attack vectors
- **test-coverage-reviewer** - Evaluates test coverage and suggests missing test cases

#### Usage in github actions

You can use [anthropics/claude-code-action](https://github.com/marketplace/actions/claude-code-action-official) to run this plugin for PR reviews in github actions.

1. Use `/install-github-app` command to setup workflow and secrets.
2. Set content of `.github/workflows/claude-code-review.yml` to the following:

```yaml
name: Claude Code Review

on:
  pull_request:
    types:
    - opened
    - synchronize # remove if want to run only, when PR is opened
    # Uncomment to limit which files can trigger the workflow
    # paths:
    #   - "**/*.ts"
    #   - "**/*.tsx"
    #   - "**/*.js"
    #   - "**/*.jsx"
    #   - "**/*.py"
    #   - "**/*.sql"
    #   - "**/*.SQL"
    #   - "**/*.sh"

jobs:
  claude-review:
    name: Claude Code Review
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: write
      id-token: write
      actions: read

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - name: Run Claude Code Review
        id: claude-review
        uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          track_progress: true # attach tracking comment
          use_sticky_comment: true

          plugin_marketplaces: https://github.com/NeoLabHQ/context-engineering-kit.git
          plugins: "code-review@context-engineering-kit\ngit@context-engineering-kit\ntdd@context-engineering-kit\nsadd@context-engineering-kit\nddd@context-engineering-kit\nsdd@context-engineering-kit\nkaizen@context-engineering-kit"

          prompt: |
            REPO: ${{ github.repository }}
            PR NUMBER: ${{ github.event.pull_request.number }}

            CRITICAL: You MUST use SlashCommand tool to read and perform /code-review:review-pr command EXACTLY!
            Do not analyze or read PR, code or anything else UNTIL you have read the command!

            Note: The PR branch is already checked out in the current working directory.

          # SlashCommand and Bash(gh pr comment:*) is required for review, the rest is optional, but recommended for better context and quality of the review.
          claude_args: '--allowed-tools "SlashCommand,Bash,Glob,Grep,Read,Task,mcp__github_inline_comment__create_inline_comment,Bash(gh issue view:*),Bash(gh search:*),Bash(gh issue list:*),Bash(gh pr comment:*),Bash(gh pr edit:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(gh pr list:*),Bash(gh api:*)"'
```

### Git

Commands for streamlined Git operations including commits and pull request creation.

**How to install**

```bash
/plugin install git@NeoLabHQ/context-engineering-kit
```

**Commands**

- `/git:commit` - Create well-formatted commits with conventional commit messages and emoji
- `/git:create-pr` - Create pull requests using GitHub CLI with proper templates and formatting
- `/git:analyze-issue` - Analyze a GitHub issue and create a detailed technical specification
- `/git:load-issues` - Load all open issues from GitHub and save them as markdown files

### Test-Driven Development

Commands and skills for test-driven development with anti-pattern detection.

**How to install**

```bash
/plugin install tdd@NeoLabHQ/context-engineering-kit
```

**Commands**

- `/tdd:write-tests` - Systematically add test coverage for local code changes using specialized review and development agents
- `/tdd:fix-tests` - Fix failing tests after business logic changes or refactoring using orchestrated agents

**Skills**

- **test-driven-development** - Introduces TDD methodology, best practices, and skills for testing using subagents

### Subagent-Driven Development

Execution framework for competitive generation, multi-agent evaluation, and subagent-driven development with quality gates.

**How to install**

```bash
/plugin install sadd@NeoLabHQ/context-engineering-kit
```

**Commands**

- `/sadd:launch-sub-agent` - Launch focused sub-agents with intelligent model selection, Zero-shot CoT reasoning, and self-critique verification
- `/sadd:do-in-parallel` - Execute the same task across multiple independent targets in parallel with context isolation
- `/sadd:do-in-steps` - Execute complex tasks through sequential sub-agent orchestration with automatic decomposition and context passing
- `/sadd:do-competitively` - Execute tasks through competitive generation, multi-judge evaluation, and evidence-based synthesis to produce superior results
- `/sadd:tree-of-thoughts` - Execute complex reasoning through systematic exploration of solution space, pruning unpromising branches, and synthesizing the best solution
- `/sadd:judge-with-debate` - Evaluate solutions through iterative multi-judge debate with consensus building or disagreement reporting
- `/sadd:judge` - Evaluate completed work using LLM-as-Judge with structured rubrics and evidence-based scoring

**Skills**

- **subagent-driven-development** - Dispatches fresh subagent for each task with code review between tasks, enabling fast iteration with quality gates
- **multi-agent-patterns** - Design multi-agent architectures (supervisor, peer-to-peer, hierarchical) for complex tasks exceeding single-agent context limits

### Domain-Driven Development

Commands for setting up domain-driven development best practices focused on code quality.

**How to install**

```bash
/plugin install ddd@NeoLabHQ/context-engineering-kit
```

**Commands**

- `/ddd:setup-code-formating` - Sets up code formatting rules and style guidelines in CLAUDE.md

**Skills**

- **software-architecture** - Includes Clean Architecture, SOLID principles, and other design patterns

### Spec-Driven Development

Comprehensive specification-driven development workflow using specialized agents.

**How to install**

```bash
/plugin install sdd@NeoLabHQ/context-engineering-kit
```

#### Usage workflow

```bash
# start claude code
claude
# setup project constitution
/sdd:00-setup Use NestJS as backend framework, strictly follow SOLID principles and Clean Architecture.

# Generate new feature specification
/sdd:01-specify Add user authentication with OAuth

# Plan feature development
/sdd:02-plan

# Create detailed implementation tasks
/sdd:03-tasks

# Execute feature implementation
/sdd:04-implement

# Document completed feature implementation
/sdd:05-document Focus on API documentation

```

**Commands**

- `/sdd:00-setup` - Create or update the project constitution from interactive or provided principle inputs
- `/sdd:01-specify` - Create or update the feature specification from a natural language feature description
- `/sdd:02-plan` - Plan the feature development based on the feature specification
- `/sdd:03-tasks` - Create detailed implementation tasks from feature plans with complexity analysis
- `/sdd:04-implement` - Execute feature implementation following task list with TDD approach and quality review
- `/sdd:05-document` - Document completed feature implementation with API guides, architecture updates, and lessons learned
- `/sdd:brainstorm` - Refines rough ideas into fully-formed designs through collaborative questioning and exploration
- `/sdd:create-ideas` - Generate diverse ideas using creative sampling based on Verbalized Sampling technique. 2-3x diversity improvement while maintaining quality.

**Agents**

- **code-architect** - Designs system architecture and technical solutions
- **code-explorer** - Navigates and understands existing codebase structure
- **code-reviewer** - Reviews implementations against specifications and quality standards

#### Theoretical Foundation

The SDD plugin implements a structured software development methodology combining proven frameworks:

- [GitHub Spec Kit](https://github.com/github/spec-kit) - Specification-driven development templates and workflows
- [OpenSpec](https://openspec.ai/) - Open specification format for software requirements
- [BMad Method](https://github.com/bmadcode/BMAD-METHOD) - Structured approach to breaking down complex features into manageable tasks

Supporting research and techniques:

- [Specification-Driven Development](https://en.wikipedia.org/wiki/Design_by_contract) - Design by contract and formal specification approaches
- [Verbalized Sampling](https://arxiv.org/abs/2510.01171) - Training-free prompting for diverse idea generation. Achieves **2-3x diversity improvement** while maintaining quality. Used for `create-ideas`, `brainstorm` and `plan` commands.

### FPF - First Principles Framework

Structured reasoning plugin implements the **[First Principles Framework (FPF)](https://github.com/ailev/FPF)** by Anatoly Levenchuk — a methodology for rigorous, auditable reasoning. The killer feature is turning the black box of AI reasoning into a transparent, evidence-backed audit trail. The plugin makes AI decision-making transparent and auditable. Instead of jumping to solutions, FPF enforces generating competing hypotheses, checking them logically, testing against evidence, then letting developers choose.

Key principles:

- **Transparent reasoning** - Full audit trail from hypothesis to decision
- **Hypothesis-driven** - Generate 3-5 competing alternatives before evaluating
- **Evidence-based** - Computed trust scores, not estimates
- **Human-in-the-loop** - AI generates options; humans decide (Transformer Mandate)

The core cycle follows three modes of inference:

1. **Abduction** — Generate competing hypotheses (don't anchor on the first idea).
2. **Deduction** — Verify logic and constraints (does the idea make sense?).
3. **Induction** — Gather evidence through tests or research (does the idea work in reality?).

Then, audit for bias, decide, and document the rationale in a durable record.

> **Warning:** This plugin loads the core FPF specification into context, which is large (~600k tokens). As a result it loaded into a subagent with Sonnet[1m] model. But such agent can consume your token limit quickly.

**How to install**

```bash
/plugin install fpf@NeoLabHQ/context-engineering-kit
```

#### Usage workflow

```bash
# Execute complete FPF cycle from hypothesis to decision
/fpf:propose-hypotheses What caching strategy should we use?

# The workflow will:
# 1. Initialize context and .fpf/ directory
# 2. Generate competing hypotheses
# 3. Allow you to add your own alternatives
# 4. Verify each against project constraints (parallel)
# 5. Validate with evidence (parallel)
# 6. Compute trust scores (parallel)
# 7. Present comparison for your decision
```

**Commands**

- `/fpf:propose-hypotheses` - Execute complete FPF cycle from hypothesis to decision (main workflow)
- `/fpf:status` - Show current FPF phase and hypothesis counts
- `/fpf:query` - Search knowledge base with assurance info
- `/fpf:decay` - Manage evidence freshness (refresh/deprecate/waive)
- `/fpf:actualize` - Reconcile knowledge with codebase changes
- `/fpf:reset` - Archive session and return to IDLE

**Agent**

- **fpf-agent** - FPF reasoning specialist for hypothesis generation, verification, validation, and trust calculus using ADI cycle and knowledge layer progression

#### Key Concepts

| Concept | Description |
|---------|-------------|
| **ADI Cycle** | Abduction-Deduction-Induction reasoning loop |
| **Knowledge Layers** | L0 (Conjecture) -> L1 (Substantiated) -> L2 (Corroborated) |
| **WLNK** | Weakest Link principle: R_eff = min(evidence_scores) |
| **Transformer Mandate** | AI generates options; humans decide |

#### Theoretical Foundation

- [FPF Repository](https://github.com/ailev/FPF) - Original methodology by Anatoly Levenchuk
- [quint-code](https://github.com/m0n0x41d/quint-code) - Implementation this plugin is based on

### Kaizen

Continuous improvement methodology inspired by Japanese philosophy and Agile practices.

**How to install**

```bash
/plugin install kaizen@NeoLabHQ/context-engineering-kit
```

**Commands**

- `/kaizen:analyse` - Auto-selects best Kaizen method (Gemba Walk, Value Stream, or Muda) for target analysis
- `/kaizen:analyse-problem` - Comprehensive A3 one-page problem analysis with root cause and action plan
- `/kaizen:why` - Iterative Five Whys root cause analysis drilling from symptoms to fundamentals
- `/kaizen:root-cause-tracing` - Systematically traces bugs backward through call stack to identify source of invalid data or incorrect behavior
- `/kaizen:cause-and-effect` - Systematic Fishbone analysis exploring problem causes across six categories
- `/kaizen:plan-do-check-act` - Iterative PDCA cycle for systematic experimentation and continuous improvement

**Skills**

- **kaizen** - Continuous improvement methodology with multiple analysis techniques

### Customaize Agent

Commands and skills for creating and refining Claude Code extensions.

**How to install**

```bash
/plugin install customaize-agent@NeoLabHQ/context-engineering-kit
```

**Commands**

- `/customaize-agent:create-agent` - Comprehensive guide for creating Claude Code agents with proper structure, triggering conditions, system prompts, and validation
- `/customaize-agent:create-command` - Interactive assistant for creating new Claude commands with proper structure and patterns
- `/customaize-agent:create-workflow-command` - Create workflow commands that orchestrate multi-step execution through sub-agents with file-based task prompts
- `/customaize-agent:create-skill` - Guide for creating effective skills with test-driven approach
- `/customaize-agent:create-hook` - Create and configure git hooks with intelligent project analysis and automated testing
- `/customaize-agent:test-skill` - Verify skills work under pressure and resist rationalization using RED-GREEN-REFACTOR cycle
- `/customaize-agent:test-prompt` - Test any prompt (commands, hooks, skills, subagent instructions) using RED-GREEN-REFACTOR cycle with subagents
- `/customaize-agent:apply-anthropic-skill-best-practices` - Comprehensive guide for skill development based on Anthropic's official best practices

**Skills**

- **prompt-engineering** - Well known prompt engineering techniques and patterns, includes Anthropic Best Practices and Agent Persuasion Principles
- **context-engineering** - Deep understanding of context mechanics: attention budget, progressive disclosure, lost-in-middle effect, and practical optimization patterns
- **agent-evaluation** - Evaluation frameworks for agent systems: LLM-as-Judge, multi-dimensional rubrics, bias mitigation, and the 95% performance finding

### Docs

Commands for project analysis and documentation management.

**How to install**

```bash
/plugin install docs@NeoLabHQ/context-engineering-kit
```

**Commands**

- `/docs:update-docs` - Update implementation documentation after completing development phases

### Tech Stack

Commands for setting up language and framework-specific best practices.

**How to install**

```bash
/plugin install tech-stack@NeoLabHQ/context-engineering-kit
```

**Commands**

- `/tech-stack:add-typescript-best-practices` - Setup TypeScript best practices and code style rules in CLAUDE.md

### MCP

Commands for integrating Model Context Protocol servers with your project. Each setup command supports configuration at multiple levels:

- **Project level (shared)** - Configuration tracked in git, shared with team via `./CLAUDE.md`
- **Project level (personal)** - Local configuration in `./CLAUDE.local.md`, not tracked in git
- **User level (global)** - Configuration in `~/.claude/CLAUDE.md`, applies to all projects

**How to install**

```bash
/plugin install mcp@NeoLabHQ/context-engineering-kit
```

**Commands**

- `/mcp:setup-context7-mcp` - Guide for setup Context7 MCP server to load documentation for specific technologies
- `/mcp:setup-serena-mcp` - Guide for setup Serena MCP server for semantic code retrieval and editing capabilities
- `/mcp:setup-codemap-cli` - Guide for setup Codemap CLI for intelligent codebase visualization and navigation
- `/mcp:setup-arxiv-mcp` - Guide for setup arXiv/Paper Search MCP server via Docker MCP for academic paper search and retrieval from multiple sources
- `/mcp:build-mcp` - Guide for creating high-quality MCP servers that enable LLMs to interact with external services
