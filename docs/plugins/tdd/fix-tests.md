# /fix-tests - Fix Failing Tests

Systematically fix all failing tests after business logic changes or refactoring using orchestrated agents.

- Purpose - Update tests to match current business logic after changes
- Output - Fixed tests that pass while preserving test intent

```bash
/fix-tests ["focus area or modules"]
```

## Arguments

Optional specification of which tests or modules to focus on. Defaults to all failing tests.

## How It Works

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

## Usage Examples

```bash
# Fix all failing tests
> /fix-tests

# Focus on specific test files
> /fix-tests user authentication tests

# Fix tests in specific module
> /fix-tests payment module tests

# Focus on integration tests
> /fix-tests integration tests only
```

## Best practices

- **Preserve test intent** - Fix assertions, not the behavior being tested
- **Avoid changing business logic** - Unless you discover an actual bug
- **Understand before fixing** - Know why the test fails before changing it
- **Run full suite** - Ensure fixes don't break other tests
- **Review agent changes** - Verify fixes maintain test quality
