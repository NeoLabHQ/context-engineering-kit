---
icon: brain-circuit
description: >-
  Advanced context engineering techniques and patterns for Claude Code, OpenCode, Cursor, Antigravity, Gemini and more.
---

# Context Engineering Kit

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
* [Core Concepts](concepts) - Understanding context engineering principles
* [Plugins List](plugins/) - Comprehensive list of all available plugins

### Agent Reliability Engineering

The three plugins in this marketplace are designed to improve how accurately and consistently the agent follows provided instructions and to reduce hallucinations and bias toward incorrect solutions. They are not competitors but rather complementary to each other, because they allow you to balance reliability vs. token cost. Here is a high-level comparison of different agent usage approaches and the probability of receiving results that are fully accurate and include zero hallucinations, based on task complexity:

<table>
<thead>
<tr>
<th rowspan="2">Approach</th>
<th colspan="4">Probability of receiving fully accurate results for the following number of changed files (p)</th>
<th rowspan="2">Tokens Overhead</th>
<th rowspan="2">What does this mean in practice</th>
</tr>
<tr>
<th>1-3</th>
<th>4-10</th>
<th>10-20</th>
<th>20+</th>
</tr>
</thead>
<tbody>
<tr>
<td>One-shot prompt</td>
<td>60%-80%</td>
<td>30%-50%</td>
<td>5%-30%</td>
<td>1%-20%</td>
<td>0</td>
<td>Accuracy depends on model, but with context growth LLM quality degrades exponentially</td>
</tr>
<tr>
<td><a href="https://neolab.gitbook.io/cek/plugins/reflexion/reflect">/reflect</a></td>
<td>68%-91%</td>
<td>49%-71%</td>
<td>13%-41%</td>
<td>1%-30%</td>
<td>1k-3k</td>
<td>Agent finds and fixes missed requirements on its own</td>
</tr>
<tr>
<td><a href="https://neolab.gitbook.io/cek/plugins/reflexion/reflect">/reflect</a> + <a href="https://neolab.gitbook.io/cek/plugins/reflexion/memorize">/memorize</a></td>
<td>79%-87%</td>
<td>60%-79%</td>
<td>34%-42%</td>
<td>5%-30%</td>
<td>2k-5k</td>
<td>Agent extracts repeatable mistakes and avoids them during new tasks</td>
</tr>
<tr>
<td><a href="https://neolab.gitbook.io/cek/plugins/sadd/do-and-judge">/do-and-judge</a></td>
<td>90%</td>
<td>83%</td>
<td>60%</td>
<td>30%</td>
<td>1.5x-3x</td>
<td>Mitigates context rot, bias, hallucinations and missed requirements using Judge sub-agent</td>
</tr>
<tr>
<td><a href="https://neolab.gitbook.io/cek/plugins/sadd/do-in-steps">/do-in-steps</a></td>
<td>92%</td>
<td>90%</td>
<td>71%</td>
<td>50%</td>
<td>3x-5x</td>
<td>Resolves all issues similar to /do-and-judge, but separately per file group</td>
</tr>
<tr>
<td><a href="https://neolab.gitbook.io/cek/plugins/sdd">/plan-task + /implement-task</a></td>
<td>94%</td>
<td>93%</td>
<td>85%</td>
<td>70%</td>
<td>5x-20x</td>
<td>Performs the /do-in-steps flow, but the specification mitigates issues caused by inconsistent architecture and codebase size</td>
</tr>
<tr>
<td><a href="https://neolab.gitbook.io/cek/plugins/sdd/brainstorm">/brainstorm</a> + <a href="https://neolab.gitbook.io/cek/plugins/sdd/plan-task">/plan-task</a> + <a href="https://neolab.gitbook.io/cek/plugins/sdd/implement-task">/implement-task</a></td>
<td>95%</td>
<td>95%</td>
<td>90%</td>
<td>80%</td>
<td>5x-20x</td>
<td>Brainstorming decreases the number of incorrect decisions and missed requirements</td>
</tr>
<tr>
<td><a href="https://neolab.gitbook.io/cek/plugins/sdd/plan-task">/plan-task</a> + human review + <a href="https://neolab.gitbook.io/cek/plugins/sdd/implement-task">/implement-task</a></td>
<td>99%</td>
<td>99%</td>
<td>99%</td>
<td>95%</td>
<td>5x-35x</td>
<td>Human review mitigates misunderstanding of requirements by LLM</td>
</tr>
</tbody>
</table>

> Reliability metrics are based on more than year of real development usage on production projects.


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

- **v3.1.0:** Improved [Spec-Driven Development plugin](https://neolab.gitbook.io/cek/plugins/sdd) generated code quality by embedding DDD/SOLID rules in the developer agent and adding a dedicated code-reviewer agent that applies functional and OOP best-practices rules together with Muda waste analysis to reduce code complexity and duplication.
- **v3.0.0:** Added support for AMP and Hermes agents. [Tech Stack plugin](https://neolab.gitbook.io/cek/plugins/tech-stack) now automatically injects typescript best practices when agent reads or writes TypeScript files.
- **v2.2.0:** [Subagent-Driven Development plugin](https://neolab.gitbook.io/cek/plugins/sadd) now works as a distilled version of [SDD plugin](https://neolab.gitbook.io/cek/plugins/sdd) using meta-judge and judge sub-agents for specification generation on the fly and in parallel to implementation. [DDD plugin](https://neolab.gitbook.io/cek/plugins/ddd) now includes Clean Architecture, DDD, SOLID, Functional Programming, and other pattern examples as rules that are automatically added to the context during code writing.
- **v2.1.0:** [Spec-Driven Development plugin](https://neolab.gitbook.io/cek/plugins/sdd) agents include high-level code quality guidelines from [DDD plugin](https://neolab.gitbook.io/cek/plugins/ddd).
- **v2.0.0:** [Spec-Driven Development plugin](https://neolab.gitbook.io/cek/plugins/sdd) was rewritten from scratch. It is now able to produce working code in 99% of cases on real-life production projects!

## Stay ahead

Star [Context Engineering Kit on GitHub](https://github.com/NeoLabHQ/context-engineering-kit) to support its development and get notified about new features and updates.

## Contributing

We welcome contributions! See our [Contributing Guide](https://github.com/NeoLabHQ/context-engineering-kit/blob/main/CONTRIBUTING.md) for details.
