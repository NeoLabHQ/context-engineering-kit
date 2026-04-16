# git-worktrees - Parallel Branch Development

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
| Compare files between worktrees | `diff <worktree1>/file <worktree2>/file` |
| Get one file from another branch | `git checkout <branch> -- <path>` |
| Cherry-pick a commit | `git cherry-pick <commit>` |

**Common Workflows**

- **Feature + Hotfix in Parallel** - Create worktree for hotfix while feature work continues
- **PR Review While Working** - Create temporary worktree to review PRs without stashing
- **Compare Implementations** - Create worktrees for different versions to diff side-by-side
- **Long-Running Tasks** - Run tests in isolated worktree while continuing development

## Creating Worktrees

Create and setup git worktrees for parallel development with automatic dependency installation.

```bash
/worktrees create <name>
/worktrees --list
```

| Argument | Description |
|----------|-------------|
| `<name>` | Branch name (multi-word supported, e.g., `auth system`), auto-detects type from keywords like feature, fix, hotfix, refactor |
| `--list` | List all existing worktrees |

**How It Works**

1. **Type Detection**: Auto-detects branch type from name (feature, fix, hotfix, refactor, etc.)
2. **Branch Resolution**: Creates or tracks existing local/remote branch
3. **Worktree Creation**: Creates sibling directory with pattern `../<project>-<name>`
4. **Dependency Installation**: Detects project type and runs appropriate install command

**Supported Project Types**: Node.js (npm/yarn/pnpm/bun), Python (pip/poetry), Rust (cargo), Go, Ruby, PHP

**Usage Examples**

```bash
# Create feature worktree (default type)
> /worktrees create auth system
# Branch: feature/auth-system -> ../myproject-auth-system

# Create fix worktree
> /worktrees create fix login error
# Branch: fix/login-error -> ../myproject-login-error

# Create hotfix while feature work continues
> /worktrees create hotfix critical bug

# List existing worktrees
> /worktrees --list
```

## Comparing Worktrees

Compare files and directories between git worktrees or worktree and current branch.

```bash
/worktrees compare [paths...] [--stat]
```

| Argument | Description |
|----------|-------------|
| `<paths>` | File(s) or directory(ies) to compare |
| `<worktree>` | Worktree path or branch name to compare |
| `--stat` | Show summary statistics only |

**Usage Examples**

```bash
# Compare specific file
> /worktrees compare src/app.js

# Compare multiple paths
> /worktrees compare src/app.js src/utils/ package.json

# Compare entire directory
> /worktrees compare src/

# Get summary statistics
> /worktrees compare --stat

# Interactive mode (lists worktrees)
> /worktrees compare
```

## Merging from Worktrees

Merge changes from worktrees into current branch with selective file checkout, cherry-picking, interactive patch selection, or manual merge.

```bash
/worktrees merge [path|commit] [--from <worktree>] [--patch] [--interactive]
```

| Argument | Description |
|----------|-------------|
| `<path\|commit>` | File path, directory, or commit SHA to merge |
| `--from <worktree>` | Source worktree path or branch name |
| `--patch` | Interactively select hunks within files |
| `--interactive` | Guided merge mode with strategy selection |

**Merge Strategies**

| Strategy | Use When | Command Pattern |
|----------|----------|-----------------|
| **Selective File** | Need complete file(s) from another branch | `git checkout <branch> -- <path>` |
| **Interactive Patch** | Need specific changes within a file | `git checkout -p <branch> -- <path>` |
| **Cherry-Pick Selective** | Need a commit but not all its changes | `git cherry-pick --no-commit` + selective staging |
| **Manual Merge** | Full branch merge with control | `git merge --no-commit` + selective staging |
| **Multi-Source** | Combining files from multiple branches | Multiple `git checkout <branch> -- <path>` |

**Usage Examples**

```bash
# Merge single file
> /worktrees merge src/app.js --from ../project-feature

# Interactive patch selection (select specific hunks)
> /worktrees merge src/utils.js --patch

# Cherry-pick specific commit
> /worktrees merge abc1234

# Full guided mode
> /worktrees merge --interactive
```
