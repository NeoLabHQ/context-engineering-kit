---
icon: brain-circuit
description: >-
  Advanced context engineering techniques and patterns for Claude Code, OpenCode, Cursor, Antigravity, Gemini and more.
---

# Context Engineering Kit

<p align="center">
  <img src="assets/Context-Engineering-Kit6.png" width="512" />
</p>


The Context Engineering Kit (CEK) is a hand-crafted collection of advanced context engineering techniques and patterns with minimal token footprint, focused on improving agent result quality and predictability.

The marketplace is based on prompts our company's developers have used daily for a long time, supplemented by plugins from benchmarked papers and high-quality projects.

## Key Features

- **Simple to Use** - Easy to install and use without any dependencies. Contains automatically used skills and self-explanatory commands.
- **Token-Efficient** - Carefully crafted prompts and architecture, preferring command-oriented skills with sub-agents over general information skills when possible, to minimize populating context with unnecessary information.
- **Quality-Focused** - Each plugin is focused on meaningfully improving agent results in a specific area.
- **Granular** - Install only the plugins you need. Each plugin loads only its specific agents, commands, and skills, without overlap or redundant skills.
- **Scientifically proven** - Plugins are based on proven techniques and patterns validated by reputable benchmarks and studies.
- **Open-Standards** - Skills are based on [agentskills.io](https://agentskills.io) specification. The [SDD](plugins/sdd/) plugin is based on the **Arc42** specification standard for software development documentation.

## Getting Started

Start here to get up and running quickly:

* [Getting Started](getting-started.md) - Installation, setup, and your first plugin
* [User Guide](guides) - Common workflows and usage patterns
* [Core Concepts](concepts.md) - Understanding context engineering principles
* [Plugins List](plugins/) - Comprehensive list of all available plugins

### Agent Reliability Engineering

The three plugins in this marketplace are designed to improve how accurately and consistently the agent follows provided instructions and to reduce hallucinations and bias toward incorrect solutions. They are not competitors but rather complementary to each other, because they allow you to balance reliability vs. token cost. Below is a high-level comparison of agent usage approaches, ordered by increasing reliability. For each approach, reliability is the probability of receiving fully accurate results with zero hallucinations on small tasks (1-3 changed files) and large tasks (20+ changed files):

1. **One-shot prompt**
   - Reliability: 60%-80% on small tasks, 1%-20% on large tasks
   - Token overhead: 0
   - In practice: accuracy depends on the model, but as context grows, LLM quality degrades exponentially.
2. **[/reflect](plugins/reflexion/reflect.md)**
   - Reliability: 68%-91% on small tasks, 1%-30% on large tasks
   - Token overhead: 1k-3k tokens
   - In practice: the agent finds and fixes missed requirements on its own.
3. **[/reflect](plugins/reflexion/reflect.md) + [/memorize](plugins/reflexion/memorize.md)**
   - Reliability: 79%-87% on small tasks, 5%-30% on large tasks
   - Token overhead: 2k-5k tokens
   - In practice: the agent extracts repeatable mistakes and avoids them during new tasks.
4. **[/do-and-judge](plugins/sadd/do-and-judge.md)**
   - Reliability: 90% on small tasks, 30% on large tasks
   - Token overhead: 1.5x-3x
   - In practice: mitigates context rot, bias, hallucinations, and missed requirements using a Judge sub-agent.
5. **[/do-in-steps](plugins/sadd/do-in-steps.md)**
   - Reliability: 92% on small tasks, 50% on large tasks
   - Token overhead: 3x-5x
   - In practice: resolves all issues similar to /do-and-judge, but separately per file group.
6. **[/plan-task + /implement-task](plugins/sdd.md)**
   - Reliability: 94% on small tasks, 70% on large tasks
   - Token overhead: 5x-20x
   - In practice: performs the /do-in-steps flow, but the specification mitigates issues caused by inconsistent architecture and codebase size.
7. **[/brainstorm](plugins/sdd/brainstorm.md) + [/plan-task](plugins/sdd/plan-task.md) + [/implement-task](plugins/sdd/implement-task.md)**
   - Reliability: 95% on small tasks, 80% on large tasks
   - Token overhead: 5x-20x
   - In practice: brainstorming decreases the number of incorrect decisions and missed requirements.
8. **[/plan-task](plugins/sdd/plan-task.md) + human review + [/implement-task](plugins/sdd/implement-task.md)**
   - Reliability: 99% on small tasks, 95% on large tasks
   - Token overhead: 5x-35x
   - In practice: human review mitigates misunderstanding of requirements by the LLM.

> Reliability metrics are based on more than a year of real development usage on production projects.


## Explore Plugins

Browse our specialized plugins organized by area of focus:

### Quality & Refinement

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td>Reflexion</td><td>Self-refinement loops</td><td><a href="plugins/reflexion/">reflexion</a></td></tr><tr><td>Code Review</td><td>Multi-agent code review system</td><td><a href="plugins/review/">review</a></td></tr><tr><td>Kaizen</td><td>Continuous improvement methodology</td><td><a href="plugins/kaizen/">kaizen</a></td></tr></tbody></table>

### Development Workflows

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td>Spec-Driven Development</td><td>Feature specification to implementation</td><td><a href="plugins/sdd/">sdd</a></td></tr><tr><td>Test-Driven Development</td><td>TDD methodology and anti-patterns</td><td><a href="plugins/tdd/">tdd</a></td></tr><tr><td>Subagent-Driven Development</td><td>Task isolation with quality gates</td><td><a href="plugins/sadd/">sadd</a></td></tr><tr><td>Domain-Driven Development</td><td>Clean Architecture and SOLID principles</td><td><a href="plugins/ddd/">ddd</a></td></tr></tbody></table>

### Developer Tools

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td>Git</td><td>Commit creation and PR management</td><td><a href="plugins/git/">git</a></td></tr><tr><td>Docs</td><td>Documentation generation and updates</td><td><a href="plugins/docs/">docs</a></td></tr><tr><td>Tech Stack</td><td>Language and framework best practices</td><td><a href="plugins/tech-stack/">tech-stack</a></td></tr></tbody></table>

### Agents Improvements and Extensions

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td>Customize Agent</td><td>Build your own commands and skills</td><td><a href="plugins/customaize-agent/">customaize-agent</a></td></tr><tr><td>MCP</td><td>Model Context Protocol server integration</td><td><a href="plugins/mcp/">mcp</a></td></tr></tbody></table>

## News

Updates from key releases:

- **v3.1.0:** Improved [Spec-Driven Development plugin](plugins/sdd/) generated code quality by embedding DDD/SOLID rules in the developer agent and adding a dedicated code-reviewer agent that applies functional and OOP best-practices rules together with Muda waste analysis to reduce code complexity and duplication.
- **v3.0.0:** Added support for AMP and Hermes agents. [Tech Stack plugin](plugins/tech-stack/) now automatically injects typescript best practices when agent reads or writes TypeScript files.
- **v2.2.0:** [Subagent-Driven Development plugin](plugins/sadd/) now works as a distilled version of [SDD plugin](plugins/sdd/) using meta-judge and judge sub-agents for specification generation on the fly and in parallel to implementation. [DDD plugin](plugins/ddd/) now includes Clean Architecture, DDD, SOLID, Functional Programming, and other pattern examples as rules that are automatically added to the context during code writing.
- **v2.1.0:** [Spec-Driven Development plugin](plugins/sdd/) agents include high-level code quality guidelines from [DDD plugin](plugins/ddd/).
- **v2.0.0:** [Spec-Driven Development plugin](plugins/sdd/) was rewritten from scratch. It is now able to produce working code in 99% of cases on real-life production projects!

## Stay ahead

Star [Context Engineering Kit on GitHub](https://github.com/NeoLabHQ/context-engineering-kit) to support its development and get notified about new features and updates.

## Contributing

We welcome contributions! See our [Contributing Guide](https://github.com/NeoLabHQ/context-engineering-kit/blob/main/CONTRIBUTING.md) for details.
