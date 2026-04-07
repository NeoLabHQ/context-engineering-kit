# /write-tests - Cover Local Changes with Tests

Systematically add test coverage for all local code changes using specialized review and development agents.

- Purpose - Ensure comprehensive test coverage for new or modified code
- Output - New test files covering all critical business logic

```bash
/write-tests ["focus area or modules"]
```

## Arguments

Optional focus area specification. Defaults to all uncommitted changes. If everything is committed, covers the latest commit.

## How It Works

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

## Usage Examples

```bash
# Cover all uncommitted changes
> /write-tests

# Focus on specific module
> /write-tests Focus on payment processing edge cases

# Cover authentication changes
> /write-tests authentication module

# Focus on error handling
> /write-tests Focus on error paths and validations
```

## Best practices

- **Run before committing** - Ensure all changes have test coverage before commit
- **Be specific** - Provide focus areas for more targeted test generation
- **Review generated tests** - Verify tests actually test behavior, not implementation
- **Iterate on gaps** - Re-run if coverage reviewer identifies missing cases
- **Prioritize critical logic** - Not every line needs 100% coverage, focus on business logic
