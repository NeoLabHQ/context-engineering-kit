# Feature Development with Quality Gates

Lightweight workflow for simple features with built-in reflection, testing, code review, and commit stages.

For complex features requiring architecture planning, use [Spec-Driven Development](./spec-driven-development.md) workflow.

## When to Use

- Simple features and enhancements
- Bug fixes and small improvements
- Refactoring existing code
- Changes that do not require architectural decisions

## Plugins needed for this workflow

- [Reflexion](../plugins/reflexion/README.md)
- [TDD](../plugins/tdd/README.md)
- [Review](../plugins/review/README.md)
- [Git](../plugins/git/README.md)

## Workflow

### How It Works

```md
┌─────────────────────────────────────────────┐
│ 1. Implement Feature                        │
│    (write code for the feature)             │
└────────────────────┬────────────────────────┘
                     │
                     │ initial implementation complete
                     ▼
┌─────────────────────────────────────────────┐
│ 2. Reflect on Implementation                │
│    (self-review and improve)                │
└────────────────────┬────────────────────────┘
                     │
                     │ identify improvements and apply them
                     ▼
┌─────────────────────────────────────────────┐
│ 3. Write Tests                              │
│    (cover changes with tests)               │
└────────────────────┬────────────────────────┘
                     │
                     │ tests passing
                     ▼
┌─────────────────────────────────────────────┐
│ 4. Review Local Changes                     │
│    (multi-agent code review)                │
└────────────────────┬────────────────────────┘
                     │
                     │ address findings if needed
                     ▼
┌─────────────────────────────────────────────┐
│ 5. Preserve Learnings                       │
│    (save insights to memory)                │
└────────────────────┬────────────────────────┘
                     │
                     │ insights saved to CLAUDE.md
                     ▼
┌─────────────────────────────────────────────┐
│ 6. Create Commit                            │
│    (conventional commit with emoji)         │
└─────────────────────────────────────────────┘
```

### 1. Implement the feature

Start by implementing your feature. Describe what you want to build and let the LLM write the code.

```bash
claude "Add email validation to user registration, then reflect"
```

After LLM completes, the `/reflexion:reflect` command will be automatically triggered to have the LLM review its own work, identify potential issues, and suggest improvements.

After it finish reflection and fixes, review the generated code to ensure it addresses your requirements before proceeding.

**Note**:

- If you not used automatic reflection in step 1, you can write `/reflexion:reflect` command manually to trigger reflection.
- If you want deeper analysis from multiple perspectives, use `/reflexion:critique` instead.

### 2. Write tests

Use the `/write-tests` command to generate tests covering the changes you made. You can optionally specify areas to focus on.

```bash
/write-tests
```

Or with specific focus areas:

```bash
/write-tests Focus on edge cases and error handling
```

After LLM completes, verify that all tests pass. If tests fail, ask the LLM to fix the issues before continuing.

### 3. Review local changes

Use the `/review-local-changes` command to run a comprehensive multi-agent code review on your uncommitted changes.

```bash
/review-local-changes
```

After LLM completes, review the findings organized by severity (Critical, High, Medium, Low). Address Critical and High priority issues before committing. You can ask the LLM to fix specific issues.

### 4. Preserve learnings

Use the `/memorize` command to save valuable insights and patterns discovered during development to your project memory.

```bash
/memorize
```

Or with specific context:

```bash
/memorize "Email validation patterns and regex considerations"
```

After LLM completes, the insights are saved to CLAUDE.md, making them available for future development sessions.

### 5. Create commit

Use the `/commit` command to create a well-formatted conventional commit with appropriate emoji.

```bash
/commit
```

After LLM completes, a commit is created with a descriptive message following conventional commit format. You can then push your changes or create a pull request using `/create-pr`.

## Tips

- **Use automatic reflection**: Add "reflect" to your prompt for automatic quality verification (e.g., `"implement feature, reflect"`)
- **Skip steps when appropriate**: For trivial changes, you may skip reflection or memorization
- **Iterate when needed**: Run reflect and review multiple times for complex changes
- **Fix before commit**: Always address Critical and High priority review findings before committing
- **Be specific**: Provide context to commands for better results (e.g., focus areas for tests)
