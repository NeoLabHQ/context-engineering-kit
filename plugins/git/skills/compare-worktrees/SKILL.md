---
name: compare-worktrees
description: Compare files and directories between git worktrees or worktree and current branch
argument-hint: Path(s) to compare, worktree paths, branch names, or --stat for summary
model: opus
allowed-tools: Bash(git worktree:*), Bash(git diff:*), Bash(git branch:*), Bash(git status:*), Bash(diff:*), Bash(ls:*), Bash(pwd:*), Bash(find:*)
---

# Claude Command: Compare Worktrees

Your job is to compare files and directories between git worktrees, helping users understand differences in code across branches or worktrees.

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
> /git:compare-worktrees src/app.js
# Prompts to select which worktree to compare with
# Shows diff of src/app.js between current and selected worktree
```

**Compare between two specific worktrees:**

```bash
> /git:compare-worktrees ../project-main ../project-feature src/module.js
# Compares src/module.js between the two specified worktrees
```

**Compare multiple files/directories:**

```bash
> /git:compare-worktrees src/app.js src/utils/ package.json
# Shows diffs for all three paths between worktrees
```

**Compare entire directories:**

```bash
> /git:compare-worktrees src/
# Shows all differences in src/ directory between worktrees
```

**Get summary statistics:**

```bash
> /git:compare-worktrees --stat
# Shows which files differ and line counts
```

**Interactive mode:**

```bash
> /git:compare-worktrees
# Lists available worktrees
# Asks which to compare
# Asks for specific paths or entire worktree
```

**Compare with branch worktree by branch name:**

```bash
> /git:compare-worktrees feature-x
# Finds worktree for feature-x branch and compares
```

**Compare specific paths between branch worktrees:**

```bash
> /git:compare-worktrees main feature-x src/ tests/
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
> /git:compare-worktrees --stat
> /git:compare-worktrees src/components/
```

### Compare Implementations

```bash
# Compare how two features implemented similar functionality
> /git:compare-worktrees ../project-feature-1 ../project-feature-2 src/auth/
```

### Quick File Check

```bash
# Check if a specific file differs
> /git:compare-worktrees package.json
```

### Pre-Merge Review

```bash
# Review all changes before merging (compare src and tests together)
> /git:compare-worktrees --stat
> /git:compare-worktrees src/ tests/
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

Use `/git:create-worktree` first to set up worktrees for comparison:

```bash
# Create worktrees for comparison
> /git:create-worktree feature-x, main
# Created: ../project-feature-x and ../project-main

# Now compare
> /git:compare-worktrees src/
```

## Troubleshooting

**"No other worktrees found"**

- Create a worktree first with `/git:create-worktree <branch>`
- Or use `git diff` for branch-only comparison without worktrees

**"Worktree for branch not found"**

- The branch may not have a worktree created
- Run `git worktree list` to see available worktrees
- Create the worktree with `/git:create-worktree <branch>`

**"Path does not exist in worktree"**

- The specified file/directory may not exist in one of the worktrees
- This could indicate the file was added/deleted in one branch
- The command will report this in the comparison output
