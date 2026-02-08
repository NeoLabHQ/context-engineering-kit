---
icon: brain-circuit
---

# Context Engineering Kit

The Context Engineering Kit (CEK) is a curated marketplace of advanced context engineering techniques and patterns designed specifically for Claude Code. It provides prompts for extensibly tested and benchmarked techniques that enhance LLM output quality, specifically focusing on code generation, research and problem solving.

## Key Features

* **Simple to Use** - Easy to install and use without any dependencies. Contains automatically used skills and self-explanatory commands.
* **Token-Efficient** - Carefully crafted prompts and architecture, preferring commands over skills, to minimize populating context with unnecessary information.
* **Quality-Focused** - Each plugin is focused on meaningfully improving agent results in a specific area.
* **Granular** - Install only the plugins you need. Each plugin loads only its specific agents, commands, and skills. Each without overlap and redundant skills.
* **Scientifically proven** - Plugins are based on proven techniques and patterns that were tested by well-trusted benchmarks and studies, with exception to development workflows that based on popular projects and frameworks.

## IDEs and CLIs support

Currently this project support only Claude Code CLI, but we plan to support other IDEs and CLIs in the future. For now you can simply copy paste prompt files in your projects. Alternatively, any support PRs are welcome.

## Getting Started

Start here to get up and running quickly:

* [Getting Started](getting-started.md) - Installation, setup, and your first plugin
* [User Guide](guides) - Common workflows and usage patterns
* [Core Concepts](concepts) - Understanding context engineering principles

## Explore Plugins

Browse our specialized plugins organized by area of focus:

### Quality & Refinement

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td>Reflexion</td><td>Self-refinement loops</td><td><a href="plugins/reflexion/">reflexion</a></td></tr><tr><td>Code Review</td><td>Multi-agent code review system</td><td><a href="plugins/code-review/">code-review</a></td></tr><tr><td>Kaizen</td><td>Continuous improvement methodology</td><td><a href="plugins/kaizen/">kaizen</a></td></tr></tbody></table>

### Development Workflows

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td>Spec-Driven Development</td><td>Feature specification to implementation</td><td><a href="plugins/sdd/">sdd</a></td></tr><tr><td>Test-Driven Development</td><td>TDD methodology and anti-patterns</td><td><a href="plugins/tdd/">tdd</a></td></tr><tr><td>Subagent-Driven Development</td><td>Task isolation with quality gates</td><td><a href="plugins/sadd/">sadd</a></td></tr><tr><td>Domain-Driven Development</td><td>Clean Architecture and SOLID principles</td><td><a href="plugins/ddd/">ddd</a></td></tr></tbody></table>

### Developer Tools

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td>Git</td><td>Commit creation and PR management</td><td><a href="plugins/git/">git</a></td></tr><tr><td>Docs</td><td>Documentation generation and updates</td><td><a href="plugins/docs/">docs</a></td></tr><tr><td>Tech Stack</td><td>Language and framework best practices</td><td><a href="plugins/tech-stack/">tech-stack</a></td></tr></tbody></table>

### Agents Improvements and Extensions

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td>Customize Agent</td><td>Build your own commands and skills</td><td><a href="plugins/customaize-agent/">customaize-agent</a></td></tr><tr><td>MCP</td><td>Model Context Protocol server integration</td><td><a href="plugins/mcp/">mcp</a></td></tr></tbody></table>

## Contributing

We welcome contributions! See our [Contributing Guide](https://github.com/NeoLabHQ/context-engineering-kit/blob/main/CONTRIBUTING.md) for details.
