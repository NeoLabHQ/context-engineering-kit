# Git Plugin

Commands for streamlined Git operations including commits and pull request creation with conventional commit messages.

## Plugin Target

- Maintain consistent commit history - Every commit follows conventional commit format
- Reduce PR creation friction - Automated formatting, templates, and linking
- Improve issue-to-code workflow - Clear technical specs from issue descriptions
- Ensure team consistency - Standardized Git operations across the team

## Overview

The Git plugin provides commands that automate and standardize Git workflows, ensuring consistent commit messages, proper PR formatting, and efficient issue management. It integrates GitHub best practices and conventional commits with emoji.

Most commands require GitHub CLI (`gh`) for full functionality including creating PRs, loading issues, and setting labels/reviewers.

## Quick Start

```bash
# Install the plugin
/plugin install git@NeoLabHQ/context-engineering-kit

# Create a well-formatted commit
> /git:commit

# Create a pull request
> /git:create-pr
```

#### Analyze Open GitHub issues

```bash
# Load all open issues
> /git:load-issues

# Analyze a GitHub issue
> /git:analyze-issue 123
```

[Usage Examples](./usage-examples.md)

## Commands Overview

### /git:commit - Conventional Commits

Create well-formatted commits with conventional commit messages and emoji.

- Purpose - Standardize commit messages across the team
- Output - Git commit with conventional format

```bash
/git:commit [flags]
```

#### Arguments

Optional flags like `--no-verify` to skip pre-commit checks.

#### How It Works

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

#### Usage Examples

```bash
# Basic commit after making changes
> git add .
> /git:commit

# Skip pre-commit hooks
> /git:commit --no-verify

# After code review
> /code-review:review-local-changes
> /git:commit
```

#### Best Practices

- Keep commits focused - One logical change per commit
- Reference issues - Include issue numbers when applicable
- Review before commit - Use code review commands first

### /git:create-pr - Pull Request Creation

Create pull requests using GitHub CLI with proper templates and formatting.

- Purpose - Streamline PR creation with consistent formatting
- Output - GitHub pull request with template

```bash
/git:create-pr
```

#### Arguments

None required - interactive guide for PR creation.

#### How It Works

1. **Branch Detection**: Identifies current branch and target base branch
2. **Template Search**: Looks for PR templates in `.github/` directory
3. **Change Summary**: Analyzes commits to generate description
4. **PR Creation**: Uses `gh pr create` with formatted content
5. **Issue Linking**: Automatically links related issues

#### Usage Examples

```bash
# Create PR for current branch
> /git:create-pr

# After completing feature
> /git:commit
> /git:create-pr

# Full workflow
> /git:analyze-issue 123
> claude "implement feature"
> /git:commit
> /git:create-pr
```

#### Best Practices

- Push branch first - Ensure branch is pushed to remote
- Use descriptive titles - Clear summary of changes
- Link issues - Reference related issues in description
- Request reviewers - Add appropriate team members

### /git:analyze-issue - Issue Analysis

Analyze a GitHub issue and create a detailed technical specification.

- Purpose - Transform issues into actionable development tasks
- Output - Technical specification with requirements

```bash
/git:analyze-issue <issue-number>
```

#### Arguments

Issue number (e.g., 42) - required.

#### How It Works

1. **Issue Fetching**: Retrieves issue details from GitHub
2. **Requirements Extraction**: Identifies user stories and acceptance criteria
3. **Technical Analysis**: Determines APIs, data models, and dependencies
4. **Task Breakdown**: Creates actionable subtasks
5. **Complexity Assessment**: Estimates implementation effort

#### Usage Examples

```bash
# Analyze issue before starting work
> /git:analyze-issue 123

# Use with SDD workflow
> /git:analyze-issue 123
> /sdd:01-specify

# Plan sprint work
> /git:load-issues
> /git:analyze-issue 45
> /git:analyze-issue 67
```

#### Best Practices

- Analyze before coding - Understand requirements first
- Check issue completeness - Request clarification if needed
- Note dependencies - Identify related issues or PRs
- Use for planning - Helps estimate and prioritize work

### /git:load-issues - Load Open Issues

Load all open issues from GitHub and save them as markdown files.

- Purpose - Bulk import issues for planning and analysis
- Output - Markdown files for each open issue

```bash
/git:load-issues
```

#### Arguments

None required - loads all open issues automatically.

#### How It Works

1. **Issue Retrieval**: Fetches all open issues from repository
2. **Content Extraction**: Parses issue title, body, labels, and metadata
3. **File Generation**: Creates markdown file for each issue
4. **Organization**: Structures files in designated directory

#### Usage Examples

```bash
# Load all issues for sprint planning
> /git:load-issues

# Then analyze specific issues
> /git:analyze-issue 123
```

#### Best Practices

- Use for sprint planning - Get overview of all open work
- Combine with analysis - Analyze high-priority issues in detail
- Regular updates - Reload periodically to stay current

### /git:attach-review-to-pr - PR Review Comments

Add line-specific review comments to pull requests using GitHub CLI API.

- Purpose - Attach detailed code review feedback to PRs
- Output - Review comments on specific lines

```bash
/git:attach-review-to-pr [pr-number]
```

#### Arguments

PR number or URL (optional - can work with current branch).

#### Usage Examples

```bash
# Add review comments to PR
> /git:attach-review-to-pr 456

# After code review
> /code-review:review-pr 456
> /git:attach-review-to-pr 456
```

### /git:create-worktree - Create Worktrees

Create and setup git worktrees for parallel development with automatic dependency installation.

- Purpose - Enable parallel branch development without stashing or context switching
- Output - New worktree with dependencies installed

```bash
/git:create-worktree <name> | --list
```

#### Arguments

- `<name>` - Descriptive name for the worktree (e.g., "refactor auth system", "fix login bug")
- `--list` - Show existing worktrees

#### How It Works

1. **Type Detection**: Auto-detects branch type from name (feature, fix, hotfix, refactor, etc.)
2. **Branch Resolution**: Creates or tracks existing local/remote branch
3. **Worktree Creation**: Creates sibling directory with pattern `../<project>-<name>`
4. **Dependency Installation**: Detects project type and runs appropriate install command

**Supported Project Types**: Node.js (npm/yarn/pnpm/bun), Python (pip/poetry), Rust (cargo), Go, Ruby, PHP

#### Usage Examples

```bash
# Create feature worktree (default type)
> /git:create-worktree auth system
# Branch: feature/auth-system → ../myproject-auth-system

# Create fix worktree
> /git:create-worktree fix login error
# Branch: fix/login-error → ../myproject-login-error

# Create hotfix while feature work continues
> /git:create-worktree hotfix critical bug

# List existing worktrees
> /git:create-worktree --list
```

### /git:compare-worktrees - Compare Worktrees

Compare files and directories between git worktrees or worktree and current branch.

- Purpose - Understand differences across branches/worktrees before merging
- Output - Diff output with clear headers and statistics

```bash
/git:compare-worktrees [paths...] [--stat]
```

#### Arguments

- `<paths>` - File(s) or directory(ies) to compare
- `<worktree>` - Worktree path or branch name to compare
- `--stat` - Show summary statistics only

#### Usage Examples

```bash
# Compare specific file
> /git:compare-worktrees src/app.js

# Compare multiple paths
> /git:compare-worktrees src/app.js src/utils/ package.json

# Compare entire directory
> /git:compare-worktrees src/

# Get summary statistics
> /git:compare-worktrees --stat

# Interactive mode (lists worktrees)
> /git:compare-worktrees
```

### /git:merge-worktree - Merge from Worktrees

Merge changes from worktrees into current branch with selective file checkout, cherry-picking, interactive patch selection, or manual merge.

- Purpose - Selectively merge changes without full branch merges
- Output - Merged files with optional cleanup

```bash
/git:merge-worktree [path|commit] [--from <worktree>] [--patch] [--interactive]
```

#### Arguments

- `<path>` - File or directory to merge
- `<commit>` - Commit name to cherry-pick
- `--from <worktree>` - Source worktree path
- `--patch` / `-p` - Interactive patch selection mode
- `--interactive` - Guided mode

#### Merge Strategies

| Strategy | Use When | Command Pattern |
|----------|----------|-----------------|
| **Selective File** | Need complete file(s) from another branch | `git checkout <branch> -- <path>` |
| **Interactive Patch** | Need specific changes within a file | `git checkout -p <branch> -- <path>` |
| **Cherry-Pick Selective** | Need a commit but not all its changes | `git cherry-pick --no-commit` + selective staging |
| **Manual Merge** | Full branch merge with control | `git merge --no-commit` + selective staging |
| **Multi-Source** | Combining files from multiple branches | Multiple `git checkout <branch> -- <path>` |

#### Usage Examples

```bash
# Merge single file
> /git:merge-worktree src/app.js --from ../project-feature

# Interactive patch selection (select specific hunks)
> /git:merge-worktree src/utils.js --patch

# Cherry-pick specific commit
> /git:merge-worktree abc1234

# Full guided mode
> /git:merge-worktree --interactive
```

## Skills Overview

### worktrees - Parallel Branch Development

Use when working on multiple branches simultaneously, context switching without stashing, reviewing PRs while developing, testing in isolation, or comparing implementations across branches.

- Purpose - Provide git worktree commands and workflow patterns for parallel development
- Core Principle - One worktree per active branch; switch contexts by changing directories

**Key Concepts**

| Concept | Description |
|---------|-------------|
| Main worktree | Original working directory from `git clone` or `git init` |
| Linked worktree | Additional directories created with `git worktree add` |
| Shared `.git` | All worktrees share same Git object database (no duplication) |
| Branch lock | Each branch can only be checked out in ONE worktree at a time |

**Quick Reference**

| Task | Command |
|------|---------|
| Create worktree (existing branch) | `git worktree add <path> <branch>` |
| Create worktree (new branch) | `git worktree add -b <branch> <path>` |
| List all worktrees | `git worktree list` |
| Remove worktree | `git worktree remove <path>` |

**Common Workflows**

- **Feature + Hotfix in Parallel** - Create worktree for hotfix while feature work continues
- **PR Review While Working** - Create temporary worktree to review PRs without stashing
- **Compare Implementations** - Create worktrees for different versions to diff side-by-side
- **Long-Running Tasks** - Run tests in isolated worktree while continuing development

### notes - Commit Metadata Annotations

Use when adding metadata to commits without changing history, tracking review status, test results, code quality annotations, or supplementing commit messages post-hoc.

- Purpose - Attach non-invasive metadata to Git objects without modifying commit history
- Core Principle - Add information to commits after creation without rewriting history

**Key Concepts**

| Concept | Description |
|---------|-------------|
| Notes ref | Storage location, default `refs/notes/commits` |
| Non-invasive | Notes never modify SHA of original object |
| Namespaces | Use `--ref` for different note categories (reviews, testing, audit) |
| Display | Notes appear in `git log` and `git show` output |

**Quick Reference**

| Task | Command |
|------|---------|
| Add note | `git notes add -m "message" <sha>` |
| View note | `git notes show <sha>` |
| Append to note | `git notes append -m "message" <sha>` |
| Use namespace | `git notes --ref=<name> <command>` |
| Push notes | `git push origin refs/notes/<name>` |

**Common Use Cases**

- **Code Review Tracking** - Mark commits as reviewed with reviewer attribution
- **Test Results Annotation** - Record test pass/fail status and coverage
- **Audit Trail** - Attach security review or compliance information
- **Sharing Notes** - Push/fetch notes to share metadata with team

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
