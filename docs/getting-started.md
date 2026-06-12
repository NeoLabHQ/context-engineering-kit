---
description: >-
  This guide will help you install Context Engineering Kit to your Claude Code
  and start using plugins.
icon: rocket
---

# Getting Started

### Step 1: Install Marketplace and Plugins

#### Claude Code

Open Claude Code and add the Context Engineering Kit marketplace

```bash
/plugin marketplace add NeoLabHQ/context-engineering-kit
```

This makes all plugins available for installation, but does not load any agents or skills into your context.

Install any plugin — for example, reflexion:

```bash
/plugin install reflexion@NeoLabHQ/context-engineering-kit
```

Each installed plugin loads only its specific agents, commands, and skills into Claude's context.

#### Cursor, Antigravity, Codex, OpenCode and others

Run the [vercel-labs/skills](https://github.com/vercel-labs/skills) command in your terminal:

```bash
npx skills add NeoLabHQ/context-engineering-kit
```
You can pick which skills and agents to install.

<details>
<summary>Alternative installation methods</summary>

You can use [OpenSkills](https://github.com/numman-ali/openskills) to install skills by running the following commands:

```bash
npx openskills install NeoLabHQ/context-engineering-kit
npx openskills sync
```

</details>

### Step 2: Use Plugin

```bash
> claude "implement user authentication"
# Claude implements user authentication, then you can ask it to reflect on implementation

> /reflect
# It analyses results and suggests improvements
# If issues are obvious, it will fix them immediately
# If they are minor, it will suggest improvements that you can respond to
> fix the issues

# If you would like to prevent issues found during reflection from appearing again,
# ask Claude to extract resolution strategies and save the insights to project memory
> /memorize
```

Alternatively, you can use the `reflect` word in the initial prompt:

```bash
> claude "implement user authentication, then reflect"
# Claude implements user authentication,
# then hook automatically runs /reflect
```

In order to use this hook, you need to have `bun` installed. However, it is not required for the overall command.

## What's Next?

* [**User Guides**](guides/) - Complete guides to using the marketplace
  * [Project Setup](guides/project-setup.md)
  * [Feature Development](guides/feature-development.md)
  * [Spec-Driven Development](guides/spec-driven-development.md)
  * [PR Review](guides/pr-review.md)
  * [CI/CD Integration](guides/ci-integration.md) - Automate code reviews with GitHub Actions

### Viewing Available Plugins

List all plugins available in the marketplace:

```bash
/plugin
```

This displays installed plugins and available plugins with their descriptions.

### Installing Plugins

Install a specific plugin from the marketplace:

```bash
# Syntax
/plugin install <plugin-name>@NeoLabHQ/context-engineering-kit

# Examples
/plugin install reflexion@NeoLabHQ/context-engineering-kit
/plugin install review@NeoLabHQ/context-engineering-kit
/plugin install sdd@NeoLabHQ/context-engineering-kit
```

### Learn More About Available Plugins

Explore the [full plugin catalog](plugins/) to find tools that match your workflow.

**Popular plugins to explore next:**

* [**Review**](plugins/review/) - Multi-agent code and PR review with specialized reviewers (security, bugs, quality, tests)
* [**Git**](plugins/git/) - Streamlined Git workflows, commit creation, PR management
* [**Spec-Driven Development**](plugins/sdd/) - Complete 6-stage workflow from specification to documentation
* [**Subagent-Driven Development**](plugins/sadd/) - Multi-agent task orchestration with quality gates between tasks
* [**Test-Driven Development**](plugins/tdd/) - TDD best practices and anti-pattern detection
* [**Kaizen**](plugins/kaizen/) - Root cause analysis using Five Whys, Fishbone diagrams, PDCA cycles

### Understand Core Concepts

Deepen your understanding of how the marketplace works:

* [**Context Engineering Concepts**](concepts.md) - Learn about the techniques behind the plugins
* [**Research Papers**](resources/papers.md) - Understand the basis for the marketplace plugins

Welcome to better AI-assisted development with Context Engineering Kit!

### Keep Your Marketplace Updated

Periodically refresh the marketplace to get the latest plugins and updates:

```bash
/plugin marketplace update NeoLabHQ/context-engineering-kit
```

### Removing Plugins

To remove a plugin and free up context:

```bash
/plugin uninstall <plugin-name>
```

This removes the plugin's commands, skills, and agents from Claude's context.
