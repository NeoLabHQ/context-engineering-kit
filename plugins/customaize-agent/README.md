# Customaize Agent Plugin

Framework for creating, testing, and optimizing Claude Code extensions including commands, skills, and hooks with built-in prompt engineering best practices.

Focused on:

- **Extension creation** - Interactive assistants for building commands, skills, and hooks with proper structure
- **TDD for prompts** - RED-GREEN-REFACTOR cycle applied to prompt engineering with subagent testing
- **Anthropic best practices** - Official guidelines for skill authoring, progressive disclosure, and discoverability
- **Prompt optimization** - Persuasion principles and token efficiency techniques

## Plugin Target

- Build reusable extensions - Create commands, skills, and hooks that follow established patterns
- Ensure prompt quality - Test prompts before deployment using isolated subagent scenarios
- Optimize for discoverability - Apply Claude Search Optimization (CSO) principles

## Overview

The Customaize Agent plugin provides a complete toolkit for extending Claude Code's capabilities. It applies Test-Driven Development principles to prompt engineering: you write test scenarios first, watch agents fail, create prompts that address those failures, and iterate until bulletproof.

The plugin is built on Anthropic's official skill authoring best practices and research-backed persuasion principles ([Prompting Science Report 3](https://arxiv.org/abs/2508.00614) - persuasion techniques more than doubled compliance rates from 33% to 72%).

## Quick Start

```bash
# Install the plugin
/plugin install customaize-agent@NeoLabHQ/context-engineering-kit

# Create a new agent
> /customaize-agent:create-agent code-reviewer "Review code for quality"

# Create a new command
> /customaize-agent:create-command validate API documentation

# Create a new skill
> /customaize-agent:create-skill image-editor

# Test a prompt before deployment
> /customaize-agent:test-prompt

# Apply Anthropic's best practices to a skill
> /customaize-agent:apply-anthropic-skill-best-practices
```

[Usage Examples](./usage-examples.md)

## Commands

- [/customaize-agent:create-agent](./create-agent.md) - Comprehensive guide for creating Claude Code agents with proper structure, triggering conditions, system prompts, and validation. Combines official Anthropic best practices with proven patterns.
- [/customaize-agent:create-command](./create-command.md) - Interactive assistant for creating new Claude commands with proper structure, patterns, and MCP tool integration.
- [/customaize-agent:create-workflow-command](./create-workflow-command.md) - Create commands that orchestrate multi-step workflows by dispatching sub-agents with task-specific instructions stored in separate files. Solves the **context bloat problem** by keeping orchestrator commands lean.
- [/customaize-agent:create-skill](./create-skill.md) - Guide for creating effective skills using a TDD-based approach. This command treats skill creation as Test-Driven Development applied to process documentation.
- [/customaize-agent:create-hook](./create-hook.md) - Analyze the project, suggest practical Claude Code hooks, and create them with proper testing. Intelligent project analysis detects tooling and suggests relevant hooks.
- [/customaize-agent:test-prompt](./test-prompt.md) - Test any prompt (commands, hooks, skills, subagent instructions) using the RED-GREEN-REFACTOR cycle with subagents for isolated testing.
- [/customaize-agent:test-skill](./test-skill.md) - Verify skills work under pressure and resist rationalization using the RED-GREEN-REFACTOR cycle. Critical for discipline-enforcing skills.
- [/customaize-agent:apply-anthropic-skill-best-practices](./apply-anthropic-skill-best-practices.md) - Comprehensive guide for skill development based on Anthropic's official best practices. Use for complex skills requiring detailed structure and optimization.

## Skills

- [prompt-engineering](./prompt-engineering.md) - Advanced prompt engineering techniques including Anthropic's official best practices and research-backed persuasion principles.
- [context-engineering](./context-engineering.md) - Use when writing, editing, or optimizing commands, skills, or sub-agent prompts. Provides deep understanding of context mechanics in agent systems.
- [agent-evaluation](./agent-evaluation.md) - Use when testing prompt effectiveness, validating context engineering choices, or measuring agent improvement quality.

## Theoretical Foundation

The Customaize Agent plugin is based on:

### Persuasion Research

- **[Prompting Science Report 3](https://arxiv.org/abs/2508.00614)** - Tested 7 persuasion principles with N=28,000 AI conversations. Persuasion techniques more than doubled compliance rates (33% to 72%, p < .001), based on related SSRN work on persuasion principles.

### Agent Skills for Context Engineering

- [Agent Skills for Context Engineering project](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) by Murat Can Koylan.
