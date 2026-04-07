# /git:commit - Conventional Commits

Create well-formatted commits with conventional commit messages and emoji.

- Purpose - Standardize commit messages across the team
- Output - Git commit with conventional format

```bash
/git:commit [flags]
```

## Arguments

Optional flags like `--no-verify` to skip pre-commit checks.

## How It Works

1. **Change Analysis**: Reviews staged changes to understand what was modified
2. **Type Detection**: Determines commit type (feat, fix, refactor, etc.)
3. **Message Generation**: Creates descriptive commit message following conventions
4. **Emoji Selection**: Adds appropriate emoji for the commit type
5. **Commit Creation**: Executes git commit with formatted message

**Commit Types with Emoji**

| Emoji | Type | Description |
|-------|------|-------------|
| ✨ | `feat` | New feature |
| 🐛 | `fix` | Bug fix |
| 📝 | `docs` | Documentation changes |
| 💄 | `style` | Code style changes (formatting) |
| ♻️ | `refactor` | Code refactoring |
| ⚡ | `perf` | Performance improvements |
| ✅ | `test` | Adding or updating tests |
| 🔧 | `chore` | Maintenance tasks |
| 🔨 | `build` | Build system changes |
| 👷 | `ci` | CI/CD changes |

## Usage Examples

```bash
# Basic commit after making changes
> git add .
> /git:commit

# Skip pre-commit hooks
> /git:commit --no-verify

# After code review
> /review-local-changes
> /git:commit
```

## Best Practices

- Keep commits focused - One logical change per commit
- Reference issues - Include issue numbers when applicable
- Review before commit - Use code review commands first

## Conventional Commit Format

The plugin follows the [conventional commits specification](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Example Commit Messages

**Feature Commit**
```
✨ feat(auth): add OAuth2 authentication

Implement OAuth2 with Google and GitHub providers
- Add OAuthController for callback handling
- Implement token exchange and validation
- Add user profile synchronization

Closes #123
```

**Bug Fix Commit**
```
🐛 fix(cart): prevent duplicate items in shopping cart

Fix race condition when adding items concurrently
- Add distributed lock for cart operations
- Implement idempotency key validation

Fixes #456
```

**Refactoring Commit**
```
♻️ refactor(order): extract order processing logic

Improve code organization and testability
- Extract OrderProcessor from OrderController
- Implement strategy pattern for order types

Related to #789
```
