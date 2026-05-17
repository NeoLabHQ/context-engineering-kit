# Test-Driven Development (TDD) Plugin

A disciplined approach to software development that ensures every line of production code is validated by tests written first. Introduces TDD methodology, anti-pattern detection, and orchestrated test coverage using specialized agents.

Focused on:

- **Test-first development** - Write tests before implementation, ensuring every feature is verified
- **Red-Green-Refactor cycle** - Systematic approach that builds confidence through failing tests
- **Anti-pattern detection** - Identifies common testing mistakes like mock abuse and test-only methods
- **Agent-orchestrated coverage** - Parallel test writing using specialized subagents for complex changes

## Plugin Target

- **Prevent regressions** - Every change is backed by tests that catch future breaks
- **Improve design quality** - Hard-to-test code reveals design problems early
- **Build confidence** - Watching tests fail then pass proves they actually test something
- **Accelerate development** - TDD is faster than debugging untested code in production

## Overview

The TDD plugin implements Kent Beck's Test-Driven Development methodology, proven over two decades to produce higher-quality, more maintainable software. The core principle is simple but transformative: **write the test first, watch it fail, then write minimal code to pass**.

The plugin is based on foundational works including Kent Beck's *Test-Driven Development: By Example* and the extensive research on TDD effectiveness.

## Quick Start

```bash
# Install the plugin
/plugin install tdd@NeoLabHQ/context-engineering-kit

> claude "Use TDD skill to implement email validation for user registration"

# Manually make some changes that cause test failures

# Fix failing tests
> /tdd:fix-tests
```

### After Implementation

If you implemented a new feature but have not written tests, you can use the `write-tests` command to cover it.

```bash
> claude "implement email validation for user registration"

# Write tests after you made changes
> /tdd:write-tests
```

[Usage Examples](./usage-examples.md)

## Commands

- [/write-tests](./write-tests.md) - Systematically add test coverage for all local code changes using specialized review and development agents
- [/fix-tests](./fix-tests.md) - Systematically fix all failing tests after business logic changes or refactoring using orchestrated agents.

## Skills

- [test-driven-development](./test-driven-development.md) - Test-Driven Development (TDD) skill. Comprehensive TDD methodology and anti-pattern detection guide that ensures rigorous test-first development.
- [design-testing-strategy](./design-testing-strategy.md) - Use when designing, planning, or reviewing a testing strategy for a feature, change, or artifact. Reference manual loaded on demand by qa-engineer, developer, code-reviewer, and judge agents that distills 15 industry sources (Test Pyramid, Testing Trophy, Google Test Sizes, ISTQB, ISO/IEC/IEEE 29119, Beck's TDD, Pact CDC, Testcontainers, Property-Based, Mutation, Risk-Based) into 7 deterministic decision gates, an enforced YAML matrix schema, and three end-to-end worked examples.

| Aspect | Value |
|--------|-------|
| **Triggers** | qa-engineer / developer / code-reviewer / sadd:judge designing tests |
| **Loaded** | On demand only (not on every prompt) |
| **Output** | `test_strategy` YAML matrix + `Test Cases to Cover` markdown list |
| **Key sections** | Decision Gates, Test Type Reference, Case Design Techniques, Dependency Decision, Strategic Skip Heuristics, Test Matrix Schema, Case Listing Schema, Worked Examples |

## Foundation

The TDD plugin is based on decades of research and practice demonstrating significant improvements in code quality and development efficiency:

### Foundational Works

- **[Test-Driven Development: By Example](https://www.oreilly.com/library/view/test-driven-development/0321146530/)** by Kent Beck - The definitive guide to TDD methodology, introducing Red-Green-Refactor
- **[Refactoring: Improving the Design of Existing Code](https://martinfowler.com/books/refactoring.html)** by Martin Fowler - Companion work on safe code transformation under test coverage
