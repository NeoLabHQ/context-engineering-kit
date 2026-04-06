---
icon: grid-4
---

# Plugins

This directory contains comprehensive documentation for all 13 plugins in the Context Engineering Kit. Each plugin is designed to enhance Claude Code with specific capabilities focused on code quality, development workflows, and continuous improvement.

## Quick Navigation

* [Reflexion](reflexion/) - Self-refinement and iterative improvement
* [Code Review](code-review/) - Multi-agent code quality analysis
* [Git](git/) - Streamlined Git operations
* [Test-Driven Development](tdd/) - TDD methodology and best practices
* [Subagent-Driven Development](sadd/) - Task delegation with quality gates
* [Domain-Driven Development](ddd/) - Code quality and architecture patterns
* [Spec-Driven Development](sdd/) - Spec-Driven workflow
* [First Principles Framework](fpf/) - Structured reasoning with ADI cycle
* [Kaizen](kaizen/) - Continuous improvement and root cause analysis
* [Customaize Agent](customaize-agent/) - Create and refine Claude Code extensions
* [Docs](docs/) - Documentation management
* [Tech Stack](tech-stack/) - Language and framework best practices
* [MCP](mcp/) - Model Context Protocol integration

## Installation

All plugins follow the same installation pattern:

```bash
# Add the marketplace (one-time setup)
/plugin marketplace add NeoLabHQ/context-engineering-kit

# Install a specific plugin
/plugin install <plugin-name>@NeoLabHQ/context-engineering-kit
```

See individual plugin documentation for specific installation commands and verification steps.

## Overview by Category

### Quality & Refinement

#### Reflexion

Self-refinement framework that introduces feedback and refinement loops to improve output quality.

**Key Features:**

* Reflect on previous responses
* Multi-perspective critique with debate
* Memory updates with insights

**When to use:** After completing any task to verify quality and identify improvements.

[Full Documentation](reflexion/)

#### Code Review

Comprehensive code review using multiple specialized agents for thorough quality evaluation.

**Key Features:**

* Multi-agent review (bug hunter, security auditor, test coverage reviewer, etc.)
* Local changes review
* Pull request review

**When to use:** Before committing changes or creating pull requests.

[Full Documentation](code-review/)

### Development Workflows

#### Test-Driven Development

TDD methodology with anti-pattern detection and testing best practices.

**Key Features:**

* TDD workflow guidance
* Common anti-patterns awareness
* Testing subagent skills

**When to use:** When implementing new features with test-first approach.

[Full Documentation](tdd/)

#### Subagent-Driven Development

Execution framework for parallel/sequential task dispatch, competitive generation, and multi-agent evaluation with quality gates.

**Key Features:**

* **Execution patterns**: parallel (`do-in-parallel`), sequential (`do-in-steps`), competitive (`do-competitively`), exploration (`tree-of-thoughts`)
* **Evaluation**: single judge (`judge`) or multi-judge debate (`judge-with-debate`)
* Fresh context isolation per task
* Quality gates with code review between tasks
* Multi-agent architecture patterns (supervisor, peer-to-peer, hierarchical)

**When to use:** For complex features requiring multiple independent tasks, competitive solution generation, or when single-agent context limits are exceeded.

[Full Documentation](sadd/)

#### Spec-Driven Development

Comprehensive Spec-Driven Development workflow using specialized agents for each phase.

**Key Features:**

* Complete workflow: setup → specify → plan → tasks → implement → document
* Multiple specialized agents (architect, explorer, reviewer, etc.)
* Constitution-based development

**When to use:** For complex features requiring detailed specifications and planning.

[Full Documentation](sdd/)

#### First Principles Framework

Structured reasoning methodology implementing the ADI (Abduction-Deduction-Induction) cycle for auditable decision-making. The FPF plugin implements structured reasoning using [the First Principles Framework](https://github.com/ailev/FPF) methodology developed by Anatoly Levenchuk a methodology for rigorous, auditable reasoning. The killer feature is turning the black box of AI reasoning into a transparent, evidence-backed audit trail. 

**Key Features:**

* Hypothesis generation with competing alternatives
* Logical verification and constraint checking
* Empirical validation with evidence tracking
* Trust calculus with Weakest Link principle
* Design Rationale Records (DRRs)
* Evidence freshness management

The core cycle follows three modes of inference:

- Abduction — Generate competing hypotheses (don't anchor on the first idea).
- Deduction — Verify logic and constraints (does the idea make sense?).
- Induction — Gather evidence through tests or research (does the idea work in reality?).

**When to use:** For architectural decisions with long-term consequences requiring auditable reasoning trails.

[Full Documentation](fpf/)

### Code Quality & Architecture

#### Domain-Driven Development

Code quality and architecture patterns including Clean Architecture and SOLID principles.

**Key Features:**

* Code formatting setup
* 14 composable rules organized into Architecture, Function Design, Explicitness, and Code Quality categories
* Covers Clean Architecture, Command-Query Separation, Functional Core/Imperative Shell, and more

**When to use:** Setting up new projects or enforcing code quality standards.

[Full Documentation](ddd/)

### Process & Analysis

#### Git

Streamlined Git operations with conventional commits, pull request management, and advanced workflow patterns.

**Key Features:**

* Conventional commits with emoji
* Pull request creation
* Issue analysis and loading
* Git worktrees for parallel branch development
* Git notes for commit metadata annotations

**When to use:** For all Git operations to maintain commit and PR quality, or when working on multiple branches simultaneously.

[Full Documentation](git/)

#### Kaizen

Continuous improvement methodology with multiple root cause analysis techniques.

**Key Features:**

* Auto-selected analysis methods
* Five Whys analysis
* A3 problem solving
* PDCA cycle

**When to use:** Investigating issues, bugs, or process improvements.

[Full Documentation](kaizen/)

### Customization & Setup

#### Customaize Agent

Tools for creating and refining Claude Code commands, skills, and hooks.

**Key Features:**

* Command creation assistant
* Skill development guide
* Prompt testing framework
* Anthropic best practices
* Context engineering fundamentals (attention budget, progressive disclosure)
* Agent evaluation frameworks (LLM-as-Judge, rubrics, bias mitigation)

**When to use:** Creating custom plugins, extending Claude Code, or optimizing agent performance.

[Full Documentation](customaize-agent/)

#### Docs

Project analysis and documentation management commands.

**Key Features:**

* Documentation updates
* Implementation tracking

**When to use:** After completing development phases to update documentation.

[Full Documentation](docs/)

#### Tech Stack

Language and framework-specific best practices setup.

**Key Features:**

* TypeScript best practices
* Framework-specific guidelines

**When to use:** Setting up new projects or enforcing language-specific standards.

[Full Documentation](tech-stack/)

#### MCP

Model Context Protocol server integration and setup.

**Key Features:**

* Context7 MCP setup
* Serena MCP setup
* MCP server development guide

**When to use:** Integrating external services with Claude Code.

[Full Documentation](mcp/)
