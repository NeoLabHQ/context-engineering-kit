---
description: >-
  This guide will help you install Context Engineering Kit to your Claude Code
  and start using plugins.
icon: rocket
---

# Getting Started

## Prerequisites

Before you begin, ensure you have:

**Claude Code installed** - The official CLI tool from Anthropic

* If not installed, visit [Claude Code documentation](https://docs.anthropic.com/claude/docs/claude-code) for installation instructions

## Quick Start

### Step 1: Add the Marketplace

First, launch Claude Code:

```bash
claude
```

Then add the Context Engineering Kit marketplace to make all plugins available:

```bash
/plugin marketplace add NeoLabHQ/context-engineering-kit
```

**What happens:**

* The marketplace metadata is downloaded and cached locally
* All available plugins become visible in your plugin list
* No plugins are installed yet - this only makes them available
* No agents, commands, or skills are loaded - your context remains clean

**Verify it worked:**

```bash
/plugin
```

You should see a list of available plugins from the marketplace, including reflexion, code-review, git, sdd, and others.

### Step 2: Install Your First Plugin

We recommend starting with the **Reflexion plugin** - it introduces feedback and refinement loops commands.

```bash
/plugin install reflexion@NeoLabHQ/context-engineering-kit
```

**What happens:**

* The Reflexion plugin is installed in your Claude Code environment
* Three new commands become available: `/reflexion:reflect`, `/reflexion:memorize`, `/reflexion:critique`
* Plugin-specific skills and agents are loaded into Claude's context in future sessions

### Step 3: Use Your First Command

Now let's see Reflexion in action. Restart Claude Code and ask Claude to help with something:

```txt
Suggest how to improve the error handling in this project
```

Claude will provide an initial response. Now, use Reflexion to ask it to reiterate on output:

```bash
/reflexion:reflect
```

**What happens:** Claude reviews its previous response using self-refinement techniques, identifies areas for improvement, and generates an enhanced version with deeper analysis.

**Expected result:** Claude will analyze its previous response critically, identify specific improvements (e.g., "I should have considered error propagation patterns"), and provide an enhanced response with more detail and better recommendations.

**Try the memorize command:**

```bash
/reflexion:memorize
```

**What happens:** Claude identifies key learnings from the interaction, updates your project's `CLAUDE.md` file with curated insights, and builds a knowledge base that future Claude sessions can leverage.

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
/plugin install code-review@NeoLabHQ/context-engineering-kit
/plugin install sdd@NeoLabHQ/context-engineering-kit
```

### Learn More About Available Plugins

Explore the [full plugin catalog](plugins/) to find tools that match your workflow.

**Popular plugins to explore next:**

* [**Code Review**](plugins/code-review/) - Multi-agent code review with specialized reviewers (security, bugs, quality, tests)
* [**Git**](plugins/git/) - Streamlined Git workflows, commit creation, PR management
* [**Spec-Driven Development**](plugins/sdd/) - Complete 6-stage workflow from specification to documentation
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
