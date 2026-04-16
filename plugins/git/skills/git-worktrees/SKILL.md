---
name: git-worktrees
description: Use when working on multiple branches simultaneously, context switching without stashing, reviewing PRs while developing, testing in isolation, or comparing implementations across branches - provides git worktree commands and workflow patterns for parallel development with multiple working directories.
---

# Git Worktrees

## Overview

Git worktrees enable checking out multiple branches simultaneously in separate directories, all sharing the same repository. Create a worktree instead of stashing changes or cloning separately.

**Core principle:** One worktree per active branch. Switch contexts by changing directories, not branches.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Main worktree** | Original working directory from `git clone` or `git init` |
| **Linked worktree** | Additional directories created with `git worktree add` |
| **Shared `.git`** | All worktrees share same Git object database (no duplication) |
| **Branch lock** | Each branch can only be checked out in ONE worktree at a time |
| **Worktree metadata** | Administrative files in `.git/worktrees/` tracking linked worktrees |

## Quick Reference

| Task | Command |
|------|---------|
| Create worktree (existing branch) | `git worktree add <path> <branch>` |
| Create worktree (new branch) | `git worktree add -b <branch> <path>` |
| Create worktree (new branch from ref) | `git worktree add -b <branch> <path> <start>` |
| Create detached worktree | `git worktree add --detach <path> <commit>` |
| List all worktrees | `git worktree list` |
| Remove worktree | `git worktree remove <path>` |
| Force remove worktree | `git worktree remove --force <path>` |
| Move worktree | `git worktree move <old> <new>` |
| Lock worktree | `git worktree lock <path>` |
| Unlock worktree | `git worktree unlock <path>` |
| Prune stale worktrees | `git worktree prune` |
| Repair worktree links | `git worktree repair` |
| Compare files between worktrees | `diff ../worktree-a/file ../worktree-b/file` |
| Get one file from another branch | `git checkout <branch> -- <path>` |
| Get partial file changes | `git checkout -p <branch> -- <path>` |
| Cherry-pick a commit | `git cherry-pick <commit>` |
| Cherry-pick without committing | `git cherry-pick --no-commit <commit>` |
| Merge without auto-commit | `git merge --no-commit <branch>` |

## Essential Commands

### Create a Worktree

```bash
# Create worktree with existing branch
git worktree add ../feature-x feature-x

# Create worktree with new branch from current HEAD
git worktree add -b new-feature ../new-feature

# Create worktree with new branch from specific commit
git worktree add -b hotfix-123 ../hotfix origin/main

# Create worktree tracking remote branch
git worktree add --track -b feature ../feature origin/feature

# Create worktree with detached HEAD (for experiments)
git worktree add --detach ../experiment HEAD~5
```

### List Worktrees

```bash
# Simple list
git worktree list

# Verbose output with additional details
git worktree list -v

# Machine-readable format (for scripting)
git worktree list --porcelain
```

**Example output:**

```
/home/user/project           abc1234 [main]
/home/user/project-feature   def5678 [feature-x]
/home/user/project-hotfix    ghi9012 [hotfix-123]
```

### Remove a Worktree

```bash
# Remove worktree (working directory must be clean)
git worktree remove ../feature-x

# Force remove (discards uncommitted changes)
git worktree remove --force ../feature-x
```

### Move a Worktree

```bash
# Relocate worktree to new path
git worktree move ../old-path ../new-path
```

### Lock/Unlock Worktrees

```bash
# Lock worktree (prevents pruning if on removable storage)
git worktree lock ../feature-x
git worktree lock --reason "On USB drive" ../feature-x

# Unlock worktree
git worktree unlock ../feature-x
```

### Prune Stale Worktrees

```bash
# Remove stale worktree metadata (after manual directory deletion)
git worktree prune

# Dry-run to see what would be pruned
git worktree prune --dry-run

# Verbose output
git worktree prune -v
```

### Repair Worktrees

```bash
# Repair worktree links after moving directories manually
git worktree repair

# Repair specific worktree
git worktree repair ../feature-x
```

## Workflow Patterns

### Pattern 1: Feature + Hotfix in Parallel

To fix a bug while feature work is in progress:

```bash
# Create worktree for hotfix from main
git worktree add -b hotfix-456 ../project-hotfix origin/main

# Switch to hotfix directory, fix, commit, push
cd ../project-hotfix
git add . && git commit -m "fix: resolve critical bug #456"
git push origin hotfix-456

# Return to feature work
cd ../project

# Clean up when done
git worktree remove ../project-hotfix
```

### Pattern 2: PR Review While Working

To review a PR without affecting current work:

```bash
# Fetch PR branch and create worktree
git fetch origin pull/123/head:pr-123
git worktree add ../project-review pr-123

# Review: run tests, inspect code
cd ../project-review

# Return to work, then clean up
cd ../project
git worktree remove ../project-review
git branch -d pr-123
```

### Pattern 3: Compare Implementations

To compare code across branches side-by-side:

```bash
# Create worktrees for different versions
git worktree add ../project-v1 v1.0.0
git worktree add ../project-v2 v2.0.0

# Diff, compare, or run both simultaneously
diff ../project-v1/src/module.js ../project-v2/src/module.js

# Clean up
git worktree remove ../project-v1
git worktree remove ../project-v2
```

### Pattern 4: Long-Running Tasks

To run tests/builds in isolation while continuing development:

```bash
# Create worktree for CI-like testing
git worktree add ../project-test main

# Start long-running tests in background
cd ../project-test && npm test &

# Continue development in main worktree
cd ../project
```

### Pattern 5: Stable Reference

To maintain a clean main checkout for reference:

```bash
# Create permanent worktree for main branch
git worktree add ../project-main main

# Lock to prevent accidental removal
git worktree lock --reason "Reference checkout" ../project-main
```

### Pattern 6: Selective Merging from Multiple Features

To combine specific changes from multiple feature branches:

```bash
# Create worktrees for each feature to review
git worktree add ../project-feature-1 feature-1
git worktree add ../project-feature-2 feature-2

# Review changes in each worktree
diff ../project/src/module.js ../project-feature-1/src/module.js
diff ../project/src/module.js ../project-feature-2/src/module.js

# From main worktree, selectively take changes
cd ../project
git checkout feature-1 -- src/moduleA.js src/utils.js
git checkout feature-2 -- src/moduleB.js
git commit -m "feat: combine selected changes from feature branches"

# Or cherry-pick specific commits
git cherry-pick abc1234  # from feature-1
git cherry-pick def5678  # from feature-2

# Clean up
git worktree remove ../project-feature-1
git worktree remove ../project-feature-2
```

## Comparing and Merging Changes Between Worktrees

Since all worktrees share the same Git repository, you can compare files, cherry-pick commits, and selectively merge changes between them.

### Compare and Review File Changes

Since worktrees are just directories, you can compare files directly:

```bash
# Compare specific file between worktrees
diff ../project-main/src/app.js ../project-feature/src/app.js

# Use git diff to compare branches (works from any worktree)
git diff main..feature-branch -- src/app.js

# Visual diff with your preferred tool
code --diff ../project-main/src/app.js ../project-feature/src/app.js

# Compare entire directories
diff -r ../project-v1/src ../project-v2/src
```

### Merge Only One File from a Worktree

You can selectively bring a single file from another branch using `git checkout`:

```bash
# In your current branch, get a specific file from another branch
git checkout feature-branch -- path/to/file.js

# Or get it from a specific commit
git checkout abc1234 -- path/to/file.js

# Get multiple specific files
git checkout feature-branch -- src/module.js src/utils.js
```

For **partial file changes** (specific hunks/lines only):

```bash
# Interactive patch mode - select which changes to take
git checkout -p feature-branch -- path/to/file.js
```

This prompts you to accept/reject each change hunk individually with options:
- `y` - apply this hunk
- `n` - skip this hunk
- `s` - split into smaller hunks
- `e` - manually edit the hunk

### Cherry-Pick Commits from Worktrees

Cherry-picking works at the commit level. Since all worktrees share the same repository, you can cherry-pick any commit:

```bash
# Find the commit hash (from any worktree or git log)
git log feature-branch --oneline

# Cherry-pick specific commit into your current branch
git cherry-pick abc1234

# Cherry-pick multiple commits
git cherry-pick abc1234 def5678

# Cherry-pick a range of commits
git cherry-pick abc1234^..def5678

# Cherry-pick without committing (stage changes only)
git cherry-pick --no-commit abc1234
```

### Merge Changes from Multiple Worktrees

You can merge or cherry-pick from multiple branches:

```bash
# Merge multiple branches sequentially
git merge feature-1
git merge feature-2

# Or use octopus merge for multiple branches at once
git merge feature-1 feature-2 feature-3

# Cherry-pick commits from multiple branches
git cherry-pick abc1234  # from feature-1
git cherry-pick def5678  # from feature-2
```

### Selective Merging - Pick Which Changes to Include

#### Option 1: Selective File Checkout

```bash
# Get specific files from different branches
git checkout feature-1 -- src/moduleA.js
git checkout feature-2 -- src/moduleB.js
git commit -m "Merge selected files from feature branches"
```

#### Option 2: Interactive Patch Selection

```bash
# Select specific hunks from a file
git checkout -p feature-1 -- src/shared.js
```

#### Option 3: Cherry-Pick with Selective Staging

```bash
# Apply changes without committing
git cherry-pick --no-commit abc1234

# Unstage what you don't want
git reset HEAD -- unwanted-file.js
git checkout -- unwanted-file.js

# Commit only what you kept
git commit -m "Selected changes from feature-1"
```

#### Option 4: Merge with Manual Selection

```bash
# Start merge but don't auto-commit
git merge --no-commit feature-1

# Review and modify staged changes
git status
git reset HEAD -- file-to-exclude.js
git checkout -- file-to-exclude.js

# Commit your selection
git commit -m "Merge selected changes from feature-1"
```

#### Option 5: Using git restore (Git 2.23+)

```bash
# Restore specific file from another branch
git restore --source=feature-branch -- path/to/file.js

# Interactive restore with patch selection
git restore -p --source=feature-branch -- path/to/file.js
```

## Directory Structure Conventions

Organize worktrees predictably:

```
~/projects/
  myproject/              # Main worktree (main/master branch)
  myproject-feature-x/    # Feature branch worktree
  myproject-hotfix/       # Hotfix worktree
  myproject-review/       # Temporary PR review worktree
```

**Naming convention:** `<project>-<purpose>` or `<project>-<branch>`

## Best Practices

| Practice | Rationale |
|----------|-----------|
| **Use sibling directories** | Keep worktrees at same level as main project for easy navigation |
| **Name by purpose** | `project-review` is clearer than `project-pr-123` |
| **Clean up promptly** | Remove worktrees when done to avoid confusion |
| **Lock remote worktrees** | Prevent pruning if worktree is on network/USB storage |
| **Use `--detach` for experiments** | Avoid creating throwaway branches |
| **Commit before removing** | Always commit or stash before `git worktree remove` |

## Common Issues and Solutions

### Issue: "Branch is already checked out"

**Cause:** Attempting to checkout a branch that's active in another worktree.

**Solution:**

```bash
# Find where the branch is checked out
git worktree list

# Either work in that worktree or remove it first
git worktree remove ../other-worktree
```

### Issue: Stale worktree after manual deletion

**Cause:** Deleted worktree directory without using `git worktree remove`.

**Solution:**

```bash
# Clean up stale metadata
git worktree prune
```

### Issue: Worktree moved manually

**Cause:** Moved worktree directory without using `git worktree move`.

**Solution:**

```bash
# Repair the worktree links
git worktree repair
# Or specify the new path
git worktree repair /new/path/to/worktree
```

### Issue: Worktree on removed drive

**Cause:** Worktree was on removable storage that's no longer connected.

**Solution:**

```bash
# If temporary, lock it to prevent pruning
git worktree lock ../usb-worktree

# If permanent, prune it
git worktree prune
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `rm -rf` to delete worktree | Always use `git worktree remove`, then `git worktree prune` if needed |
| Forgetting branch is locked to worktree | Run `git worktree list` before checkout errors |
| Not cleaning up temporary worktrees | Remove worktrees immediately after task completion |
| Creating worktrees in nested locations | Use sibling directories (`../project-feature`) not subdirs |
| Moving worktree directory manually | Use `git worktree move` or run `git worktree repair` after |

## Agent Workflow Integration

To isolate parallel agent tasks:

```bash
# Create worktree for isolated task
git worktree add -b task-123 ../project-task-123
cd ../project-task-123
# Make changes, run tests, return
cd ../project
```

To experiment safely with detached HEAD:

```bash
# Create detached worktree (no branch to clean up)
git worktree add --detach ../project-experiment
cd ../project-experiment
# Experiment, then discard or commit to new branch
git worktree remove --force ../project-experiment
```

## Verification Checklist

Before using worktrees:

- [ ] Understand that branches can only be checked out in one worktree
- [ ] Know where worktrees will be created (use sibling directories)
- [ ] Plan cleanup strategy for temporary worktrees

When creating worktrees:

- [ ] Use descriptive directory names
- [ ] Verify branch is not already checked out elsewhere
- [ ] Consider using `--detach` for experiments

When removing worktrees:

- [ ] Commit or stash any uncommitted changes
- [ ] Use `git worktree remove`, not `rm -rf`
- [ ] Run `git worktree prune` if directory was deleted manually

--- 

# How to Compare Worktrees

Workflow to compare files and directories between git worktrees, helping users understand differences in code across branches or worktrees.

## Instructions

CRITICAL: Perform the following steps exactly as described:

1. **Current state check**: Run `git worktree list` to show all existing worktrees and their locations

2. **Parse user input**: Classify each provided argument:
   - **No arguments**: Interactive mode - ask user what to compare
   - **`--stat`**: Show summary statistics of differences (files changed, insertions, deletions)
   - **Worktree path**: A path that matches one of the worktree roots from `git worktree list`
   - **Branch name**: A name that matches a branch in one of the worktrees
   - **File/directory path**: A path within the current worktree to compare

3. **Determine comparison targets** (worktrees to compare):
   a. If user provided worktree paths: Use those as comparison targets
   b. If user specified branch names: Find the worktrees for those branches from `git worktree list`
   c. If only one worktree exists besides current: Use current and that one as comparison targets
   d. If multiple worktrees exist and none specified: Present list and ask user which to compare
   e. If no other worktrees exist: Offer to compare with a branch using `git diff`

4. **Determine what to compare** (files/directories within worktrees):
   a. If user specified file(s) or directory(ies) paths: Compare ALL of them
   b. If no specific paths given: Ask user:
      - "Compare entire worktree?" or
      - "Compare specific files/directories? (enter paths)"

5. **Execute comparison**:

   **For specific files between worktrees:**

   ```bash
   diff <worktree1>/<path> <worktree2>/<path>
   # Or for unified diff format:
   diff -u <worktree1>/<path> <worktree2>/<path>
   ```

   **For directories between worktrees:**

   ```bash
   diff -r <worktree1>/<directory> <worktree2>/<directory>
   # Or for summary only:
   diff -rq <worktree1>/<directory> <worktree2>/<directory>
   ```

   **For branch-level comparison (using git diff):**

   ```bash
   git diff <branch1>..<branch2> -- <path>
   # Or for stat summary:
   git diff --stat <branch1>..<branch2>
   ```

   **For comparing with current working directory:**

   ```bash
   diff <current-file> <other-worktree>/<file>
   ```

6. **Format and present results**:
   - Show clear header indicating what's being compared
   - For large diffs, offer to show summary first
   - Highlight significant changes (new files, deleted files, renamed files)
   - Provide context about the branches each worktree contains

## Comparison Modes

| Mode | Description | Command Pattern |
|------|-------------|-----------------|
| **File diff** | Compare single file between worktrees | `diff -u <wt1>/file <wt2>/file` |
| **Directory diff** | Compare directories recursively | `diff -r <wt1>/dir <wt2>/dir` |
| **Summary only** | Show which files differ (no content) | `diff -rq <wt1>/ <wt2>/` |
| **Git diff** | Use git's diff (branch-based) | `git diff branch1..branch2 -- path` |
| **Stat view** | Show change statistics | `git diff --stat branch1..branch2` |

## Worktree Detection

The command finds worktrees using `git worktree list`:

```
/home/user/project           abc1234 [main]
/home/user/project-feature   def5678 [feature-x]
/home/user/project-hotfix    ghi9012 [hotfix-123]
```

From this output, the command extracts:

- **Path**: The absolute path to the worktree directory
- **Branch**: The branch name in brackets (used when user specifies branch name)

## Examples

**Compare specific file between worktrees:**

```bash
> /worktrees compare src/app.js
# Prompts to select which worktree to compare with
# Shows diff of src/app.js between current and selected worktree
```

**Compare between two specific worktrees:**

```bash
> /worktrees compare ../project-main ../project-feature src/module.js
# Compares src/module.js between the two specified worktrees
```

**Compare multiple files/directories:**

```bash
> /worktrees compare src/app.js src/utils/ package.json
# Shows diffs for all three paths between worktrees
```

**Compare entire directories:**

```bash
> /worktrees compare src/
# Shows all differences in src/ directory between worktrees
```

**Get summary statistics:**

```bash
> /worktrees compare --stat
# Shows which files differ and line counts
```

**Interactive mode:**

```bash
> /worktrees compare
# Lists available worktrees
# Asks which to compare
# Asks for specific paths or entire worktree
```

**Compare with branch worktree by branch name:**

```bash
> /worktrees compare feature-x
# Finds worktree for feature-x branch and compares
```

**Compare specific paths between branch worktrees:**

```bash
> /worktrees compare main feature-x src/ tests/
# Compares src/ and tests/ directories between main and feature-x worktrees
```

## Output Format

**File Comparison Header:**

```
Comparing: src/app.js
  From: /home/user/project (main)
  To:   /home/user/project-feature (feature-x)
---
[diff output]
```

**Summary Output:**

```
Worktree Comparison Summary
===========================
From: /home/user/project (main)
To:   /home/user/project-feature (feature-x)

Files only in main:
  - src/deprecated.js

Files only in feature-x:
  + src/new-feature.js
  + src/new-feature.test.js

Files that differ:
  ~ src/app.js
  ~ src/utils/helpers.js
  ~ package.json

Statistics:
  3 files changed
  2 files added
  1 file removed
```

## Common Workflows

### Review Feature Changes

```bash
# See what changed in a feature branch
> /worktrees compare --stat
> /worktrees compare src/components/
```

### Compare Implementations

```bash
# Compare how two features implemented similar functionality
> /worktrees compare ../project-feature-1 ../project-feature-2 src/auth/
```

### Quick File Check

```bash
# Check if a specific file differs
> /worktrees compare package.json
```

### Pre-Merge Review

```bash
# Review all changes before merging (compare src and tests together)
> /worktrees compare --stat
> /worktrees compare src/ tests/
# Both src/ and tests/ directories will be compared
```

## Important Notes

- **Argument detection**: The command auto-detects argument types by comparing them against `git worktree list` output:
  - Paths matching worktree roots → treated as worktrees to compare
  - Names matching branches in worktrees → treated as worktrees to compare
  - Other paths → treated as files/directories to compare within worktrees

- **Multiple paths**: When multiple file/directory paths are provided, ALL of them are compared between the selected worktrees (not just the first one).

- **Worktree paths**: When specifying worktrees, use the full path or relative path from current directory (e.g., `../project-feature`)

- **Branch vs Worktree**: If you specify a branch name, the command looks for a worktree with that branch checked out. If no worktree exists for that branch, it suggests using `git diff` instead.

- **Large diffs**: For large directories, the command will offer to show a summary first before displaying full diff output.

- **Binary files**: Binary files are detected and reported as "Binary files differ" without showing actual diff.

- **File permissions**: The diff will also show changes in file permissions if they differ.

- **No worktrees**: If no other worktrees exist, the command will explain how to create one and offer to use `git diff` for branch comparison instead.

## Integration with Create Worktree

Use `/worktrees create` first to set up worktrees for comparison:

```bash
# Create worktrees for comparison
> /worktrees create feature-x, main
# Created: ../project-feature-x and ../project-main

# Now compare
> /worktrees compare src/
```

## Troubleshooting

**"No other worktrees found"**

- Create a worktree first with `/worktrees create <branch>`
- Or use `git diff` for branch-only comparison without worktrees

**"Worktree for branch not found"**

- The branch may not have a worktree created
- Run `git worktree list` to see available worktrees
- Create the worktree with `/worktrees create <branch>`

**"Path does not exist in worktree"**

- The specified file/directory may not exist in one of the worktrees
- This could indicate the file was added/deleted in one branch
- The command will report this in the comparison output

---

# How to Create Worktree

Workflow to create and setup git worktrees for parallel development, with automatic detection and installation of project dependencies.

## Instructions

CRITICAL: Perform the following steps exactly as described:

1. **Current state check**: Run `git worktree list` to show existing worktrees and `git status` to verify the repository state is clean (no uncommitted changes that might cause issues)

2. **Fetch latest remote branches**: Run `git fetch --all` to ensure local has knowledge of all remote branches

3. **Parse user input**: Determine what the user wants to create:
   - `<name>`: Create worktree with auto-detected type prefix
   - `--list`: Just show existing worktrees and exit
   - No input: Ask user interactively for the name

4. **Auto-detect branch type from name**: Check if the first word is a known branch type. If yes, use it as the prefix and the rest as the name. If no, default to `feature/`.

   **Known types:** `feature`, `feat`, `fix`, `bug`, `bugfix`, `hotfix`, `release`, `docs`, `test`, `refactor`, `chore`, `spike`, `experiment`, `review`

   **Examples:**
   - `refactor auth system` → `refactor/auth-system`
   - `fix login bug` → `fix/login-bug`
   - `auth system` → `feature/auth-system` (default)
   - `hotfix critical error` → `hotfix/critical-error`

   **Name normalization:** Convert spaces to dashes, lowercase, remove special characters except dashes/underscores

5. **For each worktree to create**:
   a. **Branch name construction**: Build full branch name from detected type and normalized name:
      - `<prefix>/<normalized-name>` (e.g., `feature/auth-system`)

   b. **Branch resolution**: Determine if the branch exists locally, remotely, or needs to be created:
      - If branch exists locally: `git worktree add ../<project>-<name> <branch>`
      - If branch exists remotely (origin/<branch>): `git worktree add --track -b <branch> ../<project>-<name> origin/<branch>`
      - If branch doesn't exist: Ask user for base branch (default: current branch or main/master), then `git worktree add -b <branch> ../<project>-<name> <base>`

   c. **Path convention**: Use sibling directory with pattern `../<project-name>-<name>`
      - Extract project name from current directory
      - Use the normalized name (NOT the full branch with prefix)
      - Example: `feature/auth-system` → `../myproject-auth-system`

   d. **Create the worktree**: Execute the appropriate git worktree add command

   e. **Dependency detection**: Check the new worktree for dependency files and determine if setup is needed:
      - `package.json` -> Node.js project (npm/yarn/pnpm/bun)
      - `requirements.txt` or `pyproject.toml` or `setup.py` -> Python project
      - `Cargo.toml` -> Rust project
      - `go.mod` -> Go project
      - `Gemfile` -> Ruby project
      - `composer.json` -> PHP project

   f. **Package manager detection** (for Node.js projects):
      - `bun.lockb` -> Use `bun install`
      - `pnpm-lock.yaml` -> Use `pnpm install`
      - `yarn.lock` -> Use `yarn install`
      - `package-lock.json` or default -> Use `npm install`

   g. **Automatic setup**: Automatically run dependency installation:
      - cd to worktree and run the detected install command
      - Report progress: "Installing dependencies with [package manager]..."
      - If installation fails, report the error but continue with worktree creation summary

6. **Summary**: Display summary of created worktrees:
   - Worktree path
   - Branch name (full name with prefix)
   - Setup status (dependencies installed or failed)
   - Quick navigation command: `cd <worktree-path>`

## Worktree Path Convention

Worktrees are created as sibling directories to maintain organization:

```
~/projects/
  myproject/                # Main worktree (current directory)
  myproject-add-auth/       # Feature branch worktree (feature/add-auth)
  myproject-critical-bug/   # Hotfix worktree (hotfix/critical-bug)
  myproject-pr-456/         # PR review worktree (review/pr-456)
```

**Naming rules:**

- Pattern: `<project-name>-<name>` (uses the name part, NOT the full branch)
- Branch name: `<type-prefix>/<name>` (e.g., `feature/add-auth`)
- Directory name uses only the `<name>` portion for brevity

## Examples

**Feature worktree (default):**

```bash
> /worktrees create auth system
# Branch: feature/auth-system
# Creates: ../myproject-auth-system
```

**Fix worktree:**

```bash
> /worktrees create fix login error
# Branch: fix/login-error
# Creates: ../myproject-login-error
```

**Refactor worktree:**

```bash
> /worktrees create refactor api layer
# Branch: refactor/api-layer
# Creates: ../myproject-api-layer
```

**Hotfix worktree:**

```bash
> /worktrees create hotfix critical bug
# Branch: hotfix/critical-bug
# Creates: ../myproject-critical-bug
```

**List existing worktrees:**

```bash
> /worktrees list
# Shows: git worktree list output
```

## Setup Detection Examples

**Node.js project with pnpm:**

```
Detected Node.js project with pnpm-lock.yaml
Installing dependencies with pnpm...
✓ Dependencies installed successfully
```

**Python project:**

```
Detected Python project with requirements.txt
Installing dependencies with pip...
✓ Dependencies installed successfully
```

**Rust project:**

```
Detected Rust project with Cargo.toml
Building project with cargo...
✓ Project built successfully
```

## Common Workflows

### Quick Feature Branch

```bash
> /worktrees create new dashboard
# Branch: feature/new-dashboard
# Creates worktree, installs dependencies, ready to code
```

### Hotfix While Feature In Progress

```bash
# In main worktree, working on feature
> /worktrees create hotfix critical bug
# Branch: hotfix/critical-bug
# Creates separate worktree from main/master
# Fix bug in hotfix worktree
# Return to feature work when done
```

### PR Review Without Stashing

```bash
> /worktrees create review pr 123
# Branch: review/pr-123
# Creates worktree for reviewing PR
# Can run tests, inspect code
# Delete when review complete
```

### Experiment or Spike

```bash
> /worktrees create spike new architecture
# Branch: spike/new-architecture
# Creates isolated worktree for experimentation
# Discard or merge based on results
```

## Important Notes

- **Branch lock**: Each branch can only be checked out in one worktree at a time. If a branch is already checked out, the command will inform you which worktree has it.

- **Shared .git**: All worktrees share the same Git object database. Changes committed in any worktree are visible to all others.

- **Clean working directory**: The command checks for uncommitted changes and warns if present, as creating worktrees is safest with a clean state.

- **Sibling directories**: Worktrees are always created as sibling directories (using `../`) to keep the workspace organized. Never create worktrees inside the main repository.

- **Automatic dependency installation**: The command automatically detects the project type and package manager, then runs the appropriate install command without prompting.

- **Remote tracking**: For remote branches, worktrees are created with proper tracking setup (`--track` flag) so pulls/pushes work correctly.

## Cleanup

When done with a worktree, use the proper removal command:

```bash
git worktree remove ../myproject-add-auth
```

Or for a worktree with uncommitted changes:

```bash
git worktree remove --force ../myproject-add-auth
```

Never use `rm -rf` to delete worktrees - always use `git worktree remove`.

## Troubleshooting

**"Branch is already checked out"**

- Run `git worktree list` to see where the branch is checked out
- Either work in that worktree or remove it first

**"Cannot create worktree - path already exists"**

- The target directory already exists
- Either remove it or choose a different worktree path

**"Dependency installation failed"**

- Navigate to the worktree manually: `cd ../myproject-<name>`
- Run the install command directly to see full error output
- Common causes: missing system dependencies, network issues, corrupted lockfile

**"Wrong type detected"**

- The first word is used as the branch type if it's a known type
- To force a specific type, start with: `fix`, `hotfix`, `docs`, `test`, `refactor`, `chore`, `spike`, `review`
- Default type is `feature/` when first word isn't a known type

---

# How to Merge Worktree

Workflow to help users merge changes from git worktrees into their current branch, supporting multiple merge strategies from simple file checkout to selective cherry-picking.

## Instructions

CRITICAL: Perform the following steps exactly as described:

1. **Current state check**: Run `git worktree list` to show all existing worktrees and `git status` to verify working directory state

2. **Parse user input**: Determine what merge operation the user wants:
   - **`--interactive` or no arguments**: Guided interactive mode
   - **File/directory path**: Merge specific file(s) or directory from a worktree
   - **Commit name**: Cherry-pick a specific commit
   - **Branch name**: Merge from that branch's worktree
   - **`--from <worktree>`**: Specify source worktree explicitly
   - **`--patch` or `-p`**: Use interactive patch selection mode

3. **Determine source worktree/branch**:
   a. If user specified `--from <worktree>`: Use that worktree path directly
   b. If user specified a branch name: Find worktree for that branch from `git worktree list`
   c. If only one other worktree exists: Ask to confirm using it as source
   d. If multiple worktrees exist: Present list and ask user which to merge from
   e. If no other worktrees exist: Explain and offer to use branch-based merge instead

4. **Determine merge strategy**: Present options based on user's needs:

   **Strategy A: Selective File Checkout** (for specific files/directories)
   - Best for: Getting complete file(s) from another branch
   - Command: `git checkout <branch> -- <path>`

   **Strategy B: Interactive Patch Selection** (for partial file changes)
   - Best for: Selecting specific hunks/lines from a file
   - Command: `git checkout -p <branch> -- <path>`
   - Prompts user for each hunk: y (apply), n (skip), s (split), e (edit)

   **Strategy C: Cherry-Pick with Selective Staging** (for specific commits)
   - Best for: Applying a commit but excluding some changes
   - Steps:
     1. `git cherry-pick --no-commit <commit>`
     2. Review staged changes
     3. `git reset HEAD -- <unwanted-files>` to unstage
     4. `git checkout -- <unwanted-files>` to discard
     5. `git commit -m "message"`

   **Strategy D: Manual Merge with Conflicts** (for complex merges)
   - Best for: Full branch merge with control over resolution
   - Steps:
     1. `git merge --no-commit <branch>`
     2. Review all changes
     3. Selectively stage/unstage files
     4. Resolve conflicts if any
     5. `git commit -m "message"`

   **Strategy E: Multi-Worktree Selective Merge** (combining from multiple sources)
   - Best for: Taking different files from different worktrees
   - Steps:
     1. `git checkout <branch1> -- <path1>`
     2. `git checkout <branch2> -- <path2>`
     3. `git commit -m "Merge selected files from multiple branches"`

5. **Execute the selected strategy**:
   - Run pre-merge comparison if user wants to review (suggest `/worktrees compare` first)
   - Execute git commands for the chosen strategy
   - Handle any conflicts that arise
   - Confirm changes before final commit

6. **Post-merge summary**: Display what was merged:
   - Files changed/added/removed
   - Source worktree/branch
   - Merge strategy used

7. **Cleanup prompt**: After successful merge, ask:
   - "Would you like to remove any worktrees to clean up local state?"
   - If yes: List worktrees and ask which to remove
   - Execute `git worktree remove <path>` for selected worktrees
   - Remind about `git worktree prune` if needed

## Merge Strategies Reference

| Strategy | Use When | Command Pattern |
|----------|----------|-----------------|
| **Selective File** | Need complete file(s) from another branch | `git checkout <branch> -- <path>` |
| **Interactive Patch** | Need specific changes within a file | `git checkout -p <branch> -- <path>` |
| **Cherry-Pick Selective** | Need a commit but not all its changes | `git cherry-pick --no-commit` + selective staging |
| **Manual Merge** | Full branch merge with control | `git merge --no-commit` + selective staging |
| **Multi-Source** | Combining files from multiple branches | Multiple `git checkout <branch> -- <path>` |

## Examples

**Merge single file from worktree:**
```bash
> /worktrees merge src/app.js --from ../project-feature
# Prompts for merge strategy
# Executes: git checkout feature-branch -- src/app.js
```

**Interactive patch selection:**
```bash
> /worktrees merge src/utils.js --patch
# Lists available worktrees to select from
# Runs: git checkout -p feature-branch -- src/utils.js
# User selects hunks interactively (y/n/s/e)
```

**Cherry-pick specific commit:**
```bash
> /worktrees merge abc1234
# Detects commit hash
# Asks: Apply entire commit or selective?
# If selective: git cherry-pick --no-commit abc1234
# Then guides through unstaging unwanted changes
```

**Full guided mode:**
```bash
> /worktrees merge
# Lists all worktrees
# Asks what to merge (files, commits, or branches)
# Guides through appropriate strategy
# Offers cleanup at end
```

**Directory merge with conflicts:**
```bash
> /worktrees merge src/components/ --from ../project-refactor
# Strategy D: Manual merge with conflicts
# git merge --no-commit refactor-branch
# Helps resolve any conflicts
# Reviews and commits selected changes
```

## Interactive Patch Mode Guide

When using `--patch` or Strategy B, the user sees prompts for each change hunk:

```
@@ -10,6 +10,8 @@ function processData(input) {
   const result = transform(input);
+  // Added validation
+  if (!isValid(result)) throw new Error('Invalid');
   return result;
 }
Apply this hunk? [y,n,q,a,d,s,e,?]
```

| Key | Action |
|-----|--------|
| `y` | Apply this hunk |
| `n` | Skip this hunk |
| `q` | Quit (don't apply this or remaining hunks) |
| `a` | Apply this and all remaining hunks |
| `d` | Don't apply this or remaining hunks in this file |
| `s` | Split into smaller hunks |
| `e` | Manually edit the hunk |
| `?` | Show help |

## Cherry-Pick Selective Workflow

For Strategy C (cherry-picking with selective staging):

```bash
# 1. Apply commit without committing
git cherry-pick --no-commit abc1234

# 2. Check what was staged
git status

# 3. Unstage files you don't want
git reset HEAD -- path/to/unwanted.js

# 4. Discard changes to those files
git checkout -- path/to/unwanted.js

# 5. Commit the remaining changes
git commit -m "Cherry-pick selected changes from abc1234"
```

## Multi-Worktree Merge Workflow

For Strategy E (merging from multiple worktrees):

```bash
# Get files from different branches
git checkout feature-auth -- src/auth/login.js src/auth/session.js
git checkout feature-api -- src/api/endpoints.js
git checkout feature-ui -- src/components/Header.js

# Review all changes
git status
git diff --cached

# Commit combined changes
git commit -m "feat: combine auth, API, and UI improvements from feature branches"
```

## Common Workflows

### Take a Feature File Without Full Merge
```bash
> /worktrees merge src/new-feature.js --from ../project-feature
# Gets just the file, not the entire branch
```

### Partial Bugfix from Hotfix Branch
```bash
> /worktrees merge --patch src/utils.js --from ../project-hotfix
# Select only the specific bug fix hunks, not all changes
```

### Combine Multiple PRs' Changes
```bash
> /worktrees merge --interactive
# Select specific files from PR-1 worktree
# Select other files from PR-2 worktree
# Combine into single coherent commit
```

### Pre-Merge Review
```bash
# First review what will be merged
> /worktrees compare src/module.js
# Then merge with confidence
> /worktrees merge src/module.js --from ../project-feature
```

## Important Notes

- **Working directory state**: Always ensure your working directory is clean before merging. Uncommitted changes can cause conflicts.

- **Pre-merge review**: Consider using `/worktrees compare` before merging to understand what changes will be applied.

- **Conflict resolution**: If conflicts occur during merge, the command will help identify and resolve them before committing.

- **No-commit flag**: Most strategies use `--no-commit` to give you control over the final commit message and what gets included.

- **Shared repository**: All worktrees share the same Git object database, so commits made in any worktree are immediately visible to cherry-pick from any other.

- **Branch locks**: Remember that branches can only be checked out in one worktree at a time. Use branch names for merge operations rather than creating duplicate worktrees.

## Cleanup After Merge

After merging, consider cleaning up worktrees that are no longer needed:

```bash
# List worktrees
git worktree list

# Remove specific worktree (clean state required)
git worktree remove ../project-feature

# Force remove (discards uncommitted changes)
git worktree remove --force ../project-feature

# Clean up stale worktree references
git worktree prune
```

The command will prompt you about cleanup after each successful merge to help maintain a tidy workspace.

## Troubleshooting

**"Cannot merge: working directory has uncommitted changes"**
- Commit or stash your current changes first
- Or use `git stash` before merge, `git stash pop` after

**"Merge conflict in <file>"**
- The command will show conflicted files
- Open files and resolve conflicts (look for `<<<<<<<` markers)
- Stage resolved files with `git add <file>`
- Continue with `git commit`

**"Commit not found" when cherry-picking**
- Ensure the commit hash is correct
- Run `git log <branch>` in any worktree to find commits
- Commits are shared across all worktrees

**"Cannot checkout: file exists in working tree"**
- File has local modifications
- Either commit, stash, or discard local changes first
- Then retry the merge operation

**"Branch not found for worktree"**
- The specified worktree may have been removed
- Run `git worktree list` to see current worktrees
- Use `git worktree prune` to clean up stale references

## Integration with Other Commands

**Pre-merge review:**
```bash
> /worktrees compare src/
> /worktrees merge src/specific-file.js
```

**Create worktree, merge, cleanup:**
```bash
> /worktrees create feature-branch
> /worktrees compare src/
> /worktrees merge src/module.js --from ../project-feature-branch
# After merge, cleanup is offered automatically
```
