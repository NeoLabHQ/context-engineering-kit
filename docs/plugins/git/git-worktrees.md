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

**Common Workflows**

- **Feature + Hotfix in Parallel** - Create worktree for hotfix while feature work continues
- **PR Review While Working** - Create temporary worktree to review PRs without stashing
- **Compare Implementations** - Create worktrees for different versions to diff side-by-side
- **Long-Running Tasks** - Run tests in isolated worktree while continuing development
