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

## Commands Overview

### /tdd:write-tests - Cover Local Changes with Tests

Systematically add test coverage for all local code changes using specialized review and development agents.

- Purpose - Ensure comprehensive test coverage for new or modified code
- Output - New test files covering all critical business logic

```bash
/tdd:write-tests ["focus area or modules"]
```

#### Arguments

Optional focus area specification. Defaults to all uncommitted changes. If everything is committed, covers the latest commit.

#### How It Works

1. **Preparation Phase**
   - Discovers test infrastructure (test commands, coverage tools)
   - Runs full test suite to establish baseline
   - Reads project conventions and patterns

2. **Analysis Phase** (parallel)
   - Verifies single test execution capability
   - Analyzes local changes via `git status` or latest commit
   - Filters non-code files and identifies logic changes
   - Assesses complexity to determine workflow path

3. **Test Writing Phase**
   - **Simple changes** (single file, straightforward logic): Writes tests directly
   - **Complex changes** (multiple files or complex logic): Orchestrates specialized agents
     - Coverage reviewer agents analyze each file for test needs
     - Developer agents write comprehensive tests in parallel
     - Verification agents confirm coverage completeness

4. **Verification Phase**
   - Runs full test suite
   - Generates coverage report if available
   - Iterates on gaps until all critical logic is covered

**Complexity Decision:**
- 1 simple file: Write tests directly
- 2+ files or complex logic: Orchestrate parallel agents

#### Usage Examples

```bash
# Cover all uncommitted changes
> /tdd:write-tests

# Focus on specific module
> /tdd:write-tests Focus on payment processing edge cases

# Cover authentication changes
> /tdd:write-tests authentication module

# Focus on error handling
> /tdd:write-tests Focus on error paths and validations
```

#### Best practices

- **Run before committing** - Ensure all changes have test coverage before commit
- **Be specific** - Provide focus areas for more targeted test generation
- **Review generated tests** - Verify tests actually test behavior, not implementation
- **Iterate on gaps** - Re-run if coverage reviewer identifies missing cases
- **Prioritize critical logic** - Not every line needs 100% coverage, focus on business logic

### /tdd:fix-tests - Fix Failing Tests

Systematically fix all failing tests after business logic changes or refactoring using orchestrated agents.

- Purpose - Update tests to match current business logic after changes
- Output - Fixed tests that pass while preserving test intent

```bash
/tdd:fix-tests ["focus area or modules"]
```

#### Arguments

Optional specification of which tests or modules to focus on. Defaults to all failing tests.

#### How It Works

1. **Discovery Phase**
   - Reads test infrastructure configuration
   - Runs full test suite to identify all failures
   - Groups failing tests by file for parallel processing

2. **Analysis Phase**
   - Verifies ability to run individual test files
   - Understands why tests are failing (outdated expectations vs. bugs)

3. **Fixing Phase**
   - **Simple changes**: Fixes tests directly
   - **Complex changes**: Launches parallel developer agents per failing test file
   - Each agent:
     - Reads test file and TDD skill
     - Analyzes failure type (expectations, setup, or actual bug)
     - Fixes test while preserving intent
     - Iterates until test passes

4. **Verification Phase**
   - Runs full test suite after all agents complete
   - Iterates on any remaining failures
   - Continues until 100% pass rate

**Agent Decision Logic:**
- Outdated test expectations: Fix assertions
- Broken test setup/mocks: Fix setup code
- Actual business logic bug (rare): Fix logic

#### Usage Examples

```bash
# Fix all failing tests
> /tdd:fix-tests

# Focus on specific test files
> /tdd:fix-tests user authentication tests

# Fix tests in specific module
> /tdd:fix-tests payment module tests

# Focus on integration tests
> /tdd:fix-tests integration tests only
```

#### Best practices

- **Preserve test intent** - Fix assertions, not the behavior being tested
- **Avoid changing business logic** - Unless you discover an actual bug
- **Understand before fixing** - Know why the test fails before changing it
- **Run full suite** - Ensure fixes don't break other tests
- **Review agent changes** - Verify fixes maintain test quality

## Skills Overview

### test-driven-development - TDD Methodology Skill

Comprehensive TDD methodology and anti-pattern detection guide that ensures rigorous test-first development.

#### The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over. No exceptions.

#### Red-Green-Refactor Cycle

```
    ┌─────────────────┐
    │                 │
    │   RED           │
    │   Write         │◄────────────────────┐
    │   failing test  │                     │
    │                 │                     │
    └────────┬────────┘                     │
             │                              │
             │ Verify fails correctly       │
             ▼                              │
    ┌─────────────────┐                     │
    │                 │                     │
    │   GREEN         │                     │
    │   Write minimal │                     │
    │   code to pass  │                     │
    │                 │                     │
    └────────┬────────┘                     │
             │                              │
             │ Verify all tests pass        │
             ▼                              │
    ┌─────────────────┐                     │
    │                 │                     │
    │   REFACTOR      │─────────────────────┘
    │   Clean up      │    Next test
    │   (stay green)  │
    │                 │
    └─────────────────┘
```

**RED - Write Failing Test:**
- Write one minimal test showing expected behavior
- Clear, descriptive test name
- Tests real code, not mocks

**Verify RED:**
- Run test and confirm it fails
- Failure should be for expected reason (feature missing, not typo)
- Test passes immediately? Fix the test, you're testing existing behavior

**GREEN - Minimal Code:**
- Write simplest code to pass the test
- No extra features, no over-engineering
- YAGNI (You Aren't Gonna Need It)

**Verify GREEN:**
- All tests pass
- No errors or warnings
- Other tests still green

**REFACTOR:**
- Remove duplication
- Improve names
- Extract helpers
- Keep tests passing throughout

#### Testing Anti-Patterns

The skill includes comprehensive anti-pattern detection:

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Testing mock behavior | Verifies mock works, not code | Test real component or unmock |
| Test-only methods | Pollutes production class | Move to test utilities |
| Mocking without understanding | Breaks behavior test depends on | Understand dependencies first |
| Incomplete mocks | Silent failures downstream | Mirror real API completely |
| Tests as afterthought | Proves nothing about correctness | Follow TDD - tests first |

#### Common Rationalizations (Rejected)

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Already manually tested" | Ad-hoc does not equal systematic. No record, can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost fallacy. Unverified code is technical debt. |
| "TDD is dogmatic" | TDD is pragmatic. Faster than debugging in production. |

## Foundation

The TDD plugin is based on decades of research and practice demonstrating significant improvements in code quality and development efficiency:

### Foundational Works

- **[Test-Driven Development: By Example](https://www.oreilly.com/library/view/test-driven-development/0321146530/)** by Kent Beck - The definitive guide to TDD methodology, introducing Red-Green-Refactor
- **[Refactoring: Improving the Design of Existing Code](https://martinfowler.com/books/refactoring.html)** by Martin Fowler - Companion work on safe code transformation under test coverage
