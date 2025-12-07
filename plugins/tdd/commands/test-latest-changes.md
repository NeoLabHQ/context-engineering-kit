---
description: Systematically add test coverage for all local code changes using specialized review and development agents. Add tests for uncommitted changes (including untracked files), or if everything is commited, then will cover latest commit.
argument-hint: what tests or modules to focus on
---

# Cover Local Changes with Tests

## User Arguments

User can provide a what tests or modules to focus on:

```
$ARGUMENTS
```

If nothing is provided, focus on all changes in current git diff that not commited. If everything is commited, then will cover latest commit.

## Context

After implementing new features or refactoring existing code, it's critical to ensure all business logic changes are covered by tests. This command orchestrates automated test creation for local changes using coverage analysis and specialized agents.

## Goal

Achieve comprehensive test coverage for all critical business logic in local code changes.

## Important Constraints

- **Focus on critical business logic** - not every line needs 100% coverage
- **Preserve existing tests** - only add new tests, don't modify existing ones
- "Analyse complexity of changes" - 
  - if there 2 or more changed files, or one file with complex logic, then **Do not write tests yourself** - only orchestrate agents!
  - if there is only one changed file, and it's a simple change, then you can write tests yourself.

## Workflow Steps

### Preparation

1. **Read sadd skill if available**
   - If available, read the sadd skill to understand best practices for managing agents

2. **Discover test infrastructure**
   - Read @README.md and package.json (or equivalent project config)
   - Identify commands to run tests and coverage reports
   - Understand project structure and testing conventions

3. **Run all tests**
   - Execute full test suite to establish baseline

### Analysis

Do steps 4-5 in parallel using haiku agents:

4. **Verify single test execution**
   - Choose any passing test file
   - Launch haiku agent with instructions to find proper command to run this only test file
     - Ask him to iterate until you can reliably run individual tests
   - After he complete try running a specific test file if it exists
   - This ensures agents can run tests in isolation

5. **Analyze local changes**
   - Run `git status -u` to identify all changed files (including untracked files)
     - If there no uncommited changes, then run `git show --name-status` to get the list of files that were changed in the latest commit.
   - Filter out non-code files (docs, configs, etc.)
   - Launch separate haikue agent per changed file to analyze file itself, and the complexity of the changes, and prepare short summary of it.
   - Extract list of files with actual logic changes

### Test Writing

#### Simple Single File Flow

If there is only one changed file, and it's a simple change, then you can write tests yourself. Following this guidline:

1. Read TDD skill for best practices on writing tests
2. Read the target file {FILE_PATH} and understand the logic
3. Review existing test files for patterns and style, if not exists then create it.
4. Analyse which tests cases should be added to cover the changes.
5.  Create comprehensive tests for all identified cases
6.  Run the test command identified before.
7.  Iterate and fix any issues until all tests pass

Ensure tests are:
  - Clear and maintainable
  - Follow project conventions
  - Test behavior, not implementation
  - Cover edge cases and error paths

#### Multiple Files or Complex File Flow

If there are multiple changed files, or one file with complex logic, then you need to use specialized agents to cover the changes. Following this guidline:

6. **Launch `code-review:test-coverage-reviewer` agents (parallel)** (Sonnet or Opus models)
   - Launch one coverage-reviewer agent per changed file
   - Provide each agent with:
     - **Context**: What changed in this file (git diff)
     - **Target**: Which specific file to analyze
     - **Resources**: Read README and relevant documentation
     - **Goal**: Identify what test suites need to be added
     - **Output**: List of test cases needed for critical business logic
   - Collect all coverage review reports

7. **Launch `developer` agents for test file (parallel)** (Sonnet or Opus models)
   - Launch one developer agent per changed file that needs tests
   - Provide each agent with:
     - **Context**: Coverage review report for this file
     - **Target**: Which specific file to create tests for
     - **Test cases**: List from coverage-reviewer agent
     - **Guidance**: Read TDD skill (if available) for best practices on writing tests.
     - **Resources**: Read README and test examples
     - **Command**: How to run tests for this file
     - **Goal**: Create comprehensive tests for all identified cases
     - **Constraint**: Add new tests, don't modify existing logic (unless clearly broken)

8. **Verify coverage (iteration)** (Sonnet or Opus models)
   - Launch `code-review:test-coverage-reviewer` agents again per file
   - Provide:
     - **Context**: Original changes + new tests added
     - **Goal**: Verify all critical business logic is covered
     - **Output**: Confirmation or list of missing coverage

9.  **Iterate if needed**
   - If any files still lack coverage: Return to step 5
   - Launch new developer agents only for files with gaps
   - Provide specific instructions on what's still missing
   - Continue until all critical business logic is covered

10.  **Final verification**

- Run full test suite to ensure all tests pass
- Generate coverage report if available
- Verify no regressions in existing tests

## Success Criteria

- All critical business logic in changed files has test coverage ✅
- All tests pass (new and existing) ✅
- Test quality verified by coverage-reviewer agents ✅

## Agent Instructions Templates

### Coverage Review Agent (Initial Analysis)

```
Analyze the file {FILE_PATH} for test coverage needs.

Context: This file was modified in local changes:
{GIT_DIFF_OUTPUT}

Your task:
1. Read the changed file and understand the business logic
2. Identify all critical code paths that need testing:
   - New functions/methods added
   - Modified business logic
   - Edge cases and error handling
   - Integration points
3. Review existing tests (if any) to avoid duplication
4. Create a list of test cases needed, prioritized by importance:
   - CRITICAL: Core business logic, data mutations
   - IMPORTANT: Error handling, validations
   - NICE_TO_HAVE: Edge cases, performance

Output format:
- List of test cases with descriptions
- Priority level for each
- Suggested test file location
```

### Developer Agent (Test Creation)

```
Create tests for file {FILE_PATH} based on coverage analysis.

Coverage review identified these test cases:
{TEST_CASES_LIST}

Your task:
1. Read TDD skill (if available) for best practices on writing tests
2. Read @README.md for project context and testing conventions
3. Read the target file {FILE_PATH} and understand the logic
4. Review existing test files for patterns and style
5. Create comprehensive tests for all identified cases
6. Run the tests: {TEST_COMMAND}
7. Iterate until all tests pass
8. Ensure tests are:
   - Clear and maintainable
   - Follow project conventions
   - Test behavior, not implementation
   - Cover edge cases and error paths

Test command: {TEST_COMMAND}
```

### Coverage Review Agent (Verification)

```
Verify test coverage for file {FILE_PATH}.

Context: Tests were added to cover local changes in this file.

Your task:
1. Read the changed file {FILE_PATH}
2. Read the new test file(s) created
3. Verify all critical business logic is covered:
   - All new functions have tests
   - All modified logic has tests
   - Edge cases are tested
   - Error handling is tested
4. Identify any gaps in coverage
5. Confirm test quality (clear, maintainable, follows TDD principles)

Output:
- PASS: All critical business logic is covered ✅
- GAPS: List specific missing test cases that need to be added
```
