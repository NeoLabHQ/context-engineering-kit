# Collection of useful prompts from other marketplaces

## frontend-design

[x][link](https://github.com/anthropics/skills/blob/main/frontend-design/SKILL.md)

Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics.

## feature-dev

[x][link](https://github.com/anthropics/claude-code/blob/main/plugins/feature-dev/commands/feature-dev.md)
[x][code-architect](https://github.com/anthropics/claude-code/blob/main/plugins/feature-dev/agents/code-architect.md)
[x][code-explorer](https://github.com/anthropics/claude-code/blob/main/plugins/feature-dev/agents/code-explorer.md)
[x][code-reviewer](https://github.com/anthropics/claude-code/blob/main/plugins/feature-dev/agents/code-reviewer.md)

The Feature Development Plugin provides a systematic 7-phase approach to building new features. Instead of jumping straight into code, it guides you through understanding the codebase, asking clarifying questions, designing architecture, and ensuring quality—resulting in better-designed features that integrate seamlessly with your existing code.

## skill-creator

[x][link](https://github.com/anthropics/skills/blob/main/skill-creator/SKILL.md)

Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.

## writing-skills

[x][link](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md)
[x][anthropic-best-practices](https://github.com/obra/superpowers/blob/main/skills/writing-skills/anthropic-best-practices.md)
[x][graphviz-conventions](https://github.com/obra/superpowers/blob/main/skills/writing-skills/graphviz-conventions.dot)
[x][persuasion-principles](https://github.com/obra/superpowers/blob/main/skills/writing-skills/persuasion-principles.md)

Use when creating new skills, editing existing skills, or verifying skills work before deployment - applies TDD to process documentation by testing with subagents before writing, iterating until bulletproof against rationalization

## subagent-driven-development

[x][link](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md)

Use when executing implementation plans with independent tasks in the current session - dispatches fresh subagent for each task with code review between tasks, enabling fast iteration with quality gates

## test-driven-development

[x][link](https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md)

Use when implementing any feature or bugfix, before writing implementation code - write the test first, watch it fail, write minimal code to pass; ensures tests actually verify behavior by requiring failure first

## testing-anti-patterns

[x][link](https://github.com/obra/superpowers/blob/main/skills/testing-anti-patterns/SKILL.md)

Use when writing or changing tests, adding mocks, or tempted to add test-only methods to production code - prevents testing mock behavior, production pollution with test-only methods, and mocking without understanding dependencies

## testing-skills-with-subagents

[x][link](https://github.com/obra/superpowers/blob/main/skills/testing-skills-with-subagents/SKILL.md)

Use when creating or editing skills, before deployment, to verify they work under pressure and resist rationalization - applies RED-GREEN-REFACTOR cycle to process documentation by running baseline without skill, writing to address failures, iterating to close loopholes

## root-cause-tracing

[link](https://github.com/obra/superpowers/blob/main/skills/root-cause-tracing/SKILL.md)

Use when errors occur deep in execution and you need to trace back to find the original trigger - systematically traces bugs backward through call stack, adding instrumentation when needed, to identify source of invalid data or incorrect behavior=

## dispatching-parallel-agents

[link](https://github.com/obra/superpowers/blob/main/skills/dispatching-parallel-agents/SKILL.md)

Use when facing 3+ independent failures that can be investigated without shared state or dependencies - dispatches multiple Claude agents to investigate and fix independent problems concurrently

## commit-commands

- [commit](https://github.com/anthropics/claude-code/blob/main/plugins/commit-commands/commands/commit.md) - Creates a git commit with an automatically generated commit message based on staged and unstaged changes.
- [commit-push-pr](https://github.com/anthropics/claude-code/blob/main/plugins/commit-commands/commands/commit-push-pr.md) - Complete workflow command that commits, pushes, and creates a pull request in one step.

## code-review

[link](https://github.com/anthropics/claude-code/blob/main/plugins/code-review/commands/code-review.md)
[code reviewer agent](https://github.com/obra/superpowers/blob/main/agents/code-reviewer.md)

Performs automated code review on a pull request using multiple specialized agents.

## pr-review-toolkit

- [command](https://github.com/anthropics/claude-code/blob/main/plugins/pr-review-toolkit/commands/review-pr.md)
- [code-reviewer](https://github.com/anthropics/claude-code/blob/main/plugins/pr-review-toolkit/agents/code-reviewer.md)
- [code-simplifier](https://github.com/anthropics/claude-code/blob/main/plugins/pr-review-toolkit/agents/code-simplifier.md)
- [comment-analyzer](https://github.com/anthropics/claude-code/blob/main/plugins/pr-review-toolkit/agents/comment-analyzer.md)
comment-analyzer.md
- [pr-test-analyzer](https://github.com/anthropics/claude-code/blob/main/plugins/pr-review-toolkit/agents/pr-test-analyzer.md)
- [silent-failure-hunter](https://github.com/anthropics/claude-code/blob/main/plugins/pr-review-toolkit/agents/silent-failure-hunter.md)
- [type-design-analyzer](https://github.com/anthropics/claude-code/blob/main/plugins/pr-review-toolkit/agents/type-design-analyzer.md)

A comprehensive collection of specialized agents for thorough pull request review, covering code comments, test coverage, error handling, type design, code quality, and code simplification.

## mcp-builder

[link](https://github.com/anthropics/skills/blob/main/mcp-builder/SKILL.md)

Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).

## prompt-engineering-patterns

[link](https://github.com/wshobson/agents/blob/main/plugins/llm-application-dev/skills/prompt-engineering-patterns/SKILL.md)

Master advanced prompt engineering techniques to maximize LLM performance, reliability, and controllability in production. Use when optimizing prompts, improving LLM outputs, or designing production prompt templates.

## brainstorming

[link](https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md)

Use when creating or developing, before writing code or implementation plans - refines rough ideas into fully-formed designs through collaborative questioning, alternative exploration, and incremental validation. Don't use during clear 'mechanical' processes
