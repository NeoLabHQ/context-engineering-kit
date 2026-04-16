# Commands Reference

Complete alphabetical index of all commands available across all Context Engineering Kit plugins.

## Commands by Plugin

### Reflexion

Reflection and self-improvement commands based on Self-Refine and Reflexion papers. [More info](../plugins/reflexion/README.md).

- `/reflexion:reflect` - Reflect on previous response and output, based on Self-refinement framework for iterative improvement with complexity triage and verification.
- `/reflexion:memorize` - Memorize insights from reflections and updates CLAUDE.md file with this knowledge. Curates insights from reflections and critiques into CLAUDE.md using Agentic Context Engineering.
- `/reflexion:critique` - Comprehensive multi-perspective review using specialized judges with debate and consensus building.


### Code Review

Comprehensive code review commands using specialized agents. [More info](../plugins/review/README.md).

- `/review-local-changes` - Comprehensive review of local uncommitted changes using specialized agents with code improvement suggestions.
- `/review-pr` - Comprehensive pull request review using specialized agents.

### Git

Commands for Git operations including commits, pull requests, and worktree management. [More info](../plugins/git/README.md).

- `/commit` - Create well-formatted commits with conventional commit messages and emoji.
- `/create-pr` - Create pull requests using GitHub CLI with proper templates and formatting.
- `/analyze-issue` - Analyze a GitHub issue and create a detailed technical specification.
- `/load-issues` - Load all open issues from GitHub and save them as markdown files.

### Spec-Driven Development (SDD)

Complete Spec-Driven Development workflow commands. [More info](../plugins/sdd/README.md).

- `/brainstorm` - Refines rough ideas into fully-formed designs through collaborative questioning and exploration
- `/add-task` - Create task template file with initial prompt
- `/plan-task` - Analyze prompt, generate required skills and refine task specification
- `/implement-task` - Execute feature implementation following task list with TDD approach and quality review

### Kaizen

Continuous improvement and problem analysis commands. [More info](../plugins/kaizen/README.md).

- `/analyse` - Auto-selects best Kaizen method (Gemba Walk, Value Stream, or Muda) for target analysis.
- `/analyse-problem` - Comprehensive A3 one-page problem analysis with root cause and action plan.
- `/why` - Iterative Five Whys root cause analysis drilling from symptoms to fundamentals.
- `/root-cause-tracing` - Systematically traces bugs backward through call stack to identify source of invalid data or incorrect behavior.
- `/cause-and-effect` - Systematic Fishbone analysis exploring problem causes across six categories.
- `/plan-do-check-act` - Iterative PDCA cycle for systematic experimentation and continuous improvement.

### Customaize Agent

Commands for creating and testing custom Claude Code extensions. [More info](../plugins/customaize-agent/README.md).

- `/create-agent` - Comprehensive guide for creating Claude Code agents with proper structure, triggering conditions, system prompts, and validation
- `/create-command` - Interactive assistant for creating new Claude commands with proper structure and patterns
- `/create-workflow-command` - Create workflow commands that orchestrate multi-step execution through sub-agents with file-based task prompts
- `/create-skill` - Guide for creating effective skills with test-driven approach
- `/create-hook` - Create and configure git hooks with intelligent project analysis and automated testing
- `/test-skill` - Verify skills work under pressure and resist rationalization using RED-GREEN-REFACTOR cycle
- `/test-prompt` - Test any prompt (commands, hooks, skills, subagent instructions) using RED-GREEN-REFACTOR cycle with subagents
- `/apply-anthropic-skill-best-practices` - Comprehensive guide for skill development based on Anthropic's official best practices

### Test-Driven Development (TDD)

Test-first development methodology with agent-orchestrated coverage. [More info](../plugins/tdd/README.md).

- `/write-tests` - Systematically add test coverage for local code changes using specialized review and development agents
- `/fix-tests` - Fix failing tests after business logic changes or refactoring using orchestrated agents

### Subagent-Driven Development (SADD)

Execution framework for parallel/sequential task dispatch, competitive generation, and multi-agent evaluation. [More info](../plugins/sadd/README.md).

#### Execution Commands

- `/launch-sub-agent` - Launch focused sub-agents with intelligent model selection, Zero-shot CoT reasoning, and self-critique verification
- `/do-and-judge` - Execute a single task with implementation sub-agent, independent judge verification, and automatic retry loop until passing
- `/do-in-parallel` - Execute the same task across multiple independent targets in parallel with context isolation
- `/do-in-steps` - Execute complex tasks through sequential sub-agent orchestration with automatic decomposition and context passing
- `/do-competitively` - Execute tasks through competitive generation, multi-judge evaluation, and evidence-based synthesis to produce superior results
- `/tree-of-thoughts` - Execute complex reasoning through systematic exploration of solution space, pruning unpromising branches, and synthesizing the best solution

#### Evaluation Commands

- `/judge-with-debate` - Evaluate solutions through iterative multi-judge debate with consensus building or disagreement reporting
- `/judge` - Evaluate completed work using LLM-as-Judge with structured rubrics and evidence-based scoring

### Docs

Documentation management commands. [More info](../plugins/docs/README.md).

- `/update-docs` - Update implementation documentation after completing development phases
- `/write-concisely` - Apply *The Elements of Style* principles to make documentation clearer and more professional

### Domain-Driven Development (DDD)

Commands for setting up domain-driven development practices. [More info](../plugins/ddd/README.md).

- `/setup-code-formating` - Sets up code formatting rules and style guidelines in CLAUDE.md

### Tech Stack

Commands for language and framework-specific best practices. [More info](../plugins/tech-stack/README.md).

- `/add-typescript-best-practices` - Setup TypeScript best practices and code style rules in CLAUDE.md

### MCP

Commands for integrating Model Context Protocol servers. [More info](../plugins/mcp/README.md).

- `/setup-context7-mcp` - Guide for setting up the Context7 MCP server to load documentation for specific technologies.
- `/setup-serena-mcp` - Guide for setting up the Serena MCP server for semantic code retrieval and editing capabilities.
- `/build-mcp` - Guide for creating high-quality MCP servers that enable LLMs to interact with external services.

### First Principles Framework (FPF)

Structured reasoning with ADI (Abduction-Deduction-Induction) cycle for auditable decision-making. [More info](../plugins/fpf/README.md).

#### Workflow Command

- `/propose-hypotheses` - Execute complete FPF reasoning cycle from hypothesis generation to decision. Orchestrates the full ADI cycle: initialize context, generate hypotheses, verify logic, validate evidence, audit trust, and produce a Design Rationale Record (DRR).

#### Utility Commands

- `/status` - Show current FPF phase and hypothesis counts across knowledge layers (L0/L1/L2).
- `/query` - Search the FPF knowledge base and display hypothesis details with assurance information.
- `/decay` - Manage evidence freshness: refresh stale evidence, deprecate obsolete decisions, or waive with documented rationale.
- `/actualize` - Reconcile the FPF knowledge base with codebase changes, detecting context drift and stale evidence.
- `/reset` - Archive current session and reset the FPF cycle for a fresh start.
