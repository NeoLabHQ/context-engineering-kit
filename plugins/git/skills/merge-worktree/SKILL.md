---
name: merge-worktree
description: Merge changes from worktrees into current branch with selective file checkout, cherry-picking, interactive patch selection, or manual merge
argument-hint: file/directory path, commit name, branch name, or --interactive for guided mode
model: opus
allowed-tools: Bash(git worktree:*), Bash(git branch:*), Bash(git diff:*), Bash(git status:*), Bash(git checkout:*), Bash(git cherry-pick:*), Bash(git merge:*), Bash(git reset:*), Bash(git log:*), Bash(git restore:*), Bash(git add:*), Bash(ls:*), Bash(pwd:*), Bash(diff:*)
---

# Claude Command: Merge Worktree

Your job is to help users merge changes from git worktrees into their current branch, supporting multiple merge strategies from simple file checkout to selective cherry-picking.

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
   - Run pre-merge comparison if user wants to review (suggest `/git:compare-worktrees` first)
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
> /git:merge-worktree src/app.js --from ../project-feature
# Prompts for merge strategy
# Executes: git checkout feature-branch -- src/app.js
```

**Interactive patch selection:**
```bash
> /git:merge-worktree src/utils.js --patch
# Lists available worktrees to select from
# Runs: git checkout -p feature-branch -- src/utils.js
# User selects hunks interactively (y/n/s/e)
```

**Cherry-pick specific commit:**
```bash
> /git:merge-worktree abc1234
# Detects commit hash
# Asks: Apply entire commit or selective?
# If selective: git cherry-pick --no-commit abc1234
# Then guides through unstaging unwanted changes
```

**Merge from multiple worktrees:**
```bash
> /git:merge-worktree --interactive
# "Select files to merge from different worktrees:"
# "From feature-1: src/moduleA.js"
# "From feature-2: src/moduleB.js, src/moduleC.js"
# Executes selective checkouts from each
```

**Full guided mode:**
```bash
> /git:merge-worktree
# Lists all worktrees
# Asks what to merge (files, commits, or branches)
# Guides through appropriate strategy
# Offers cleanup at end
```

**Directory merge with conflicts:**
```bash
> /git:merge-worktree src/components/ --from ../project-refactor
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
> /git:merge-worktree src/new-feature.js --from ../project-feature
# Gets just the file, not the entire branch
```

### Partial Bugfix from Hotfix Branch
```bash
> /git:merge-worktree --patch src/utils.js --from ../project-hotfix
# Select only the specific bug fix hunks, not all changes
```

### Combine Multiple PRs' Changes
```bash
> /git:merge-worktree --interactive
# Select specific files from PR-1 worktree
# Select other files from PR-2 worktree
# Combine into single coherent commit
```

### Pre-Merge Review
```bash
# First review what will be merged
> /git:compare-worktrees src/module.js
# Then merge with confidence
> /git:merge-worktree src/module.js --from ../project-feature
```

## Important Notes

- **Working directory state**: Always ensure your working directory is clean before merging. Uncommitted changes can cause conflicts.

- **Pre-merge review**: Consider using `/git:compare-worktrees` before merging to understand what changes will be applied.

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
> /git:compare-worktrees src/
> /git:merge-worktree src/specific-file.js
```

**Create worktree, merge, cleanup:**
```bash
> /git:create-worktree feature-branch
> /git:compare-worktrees src/
> /git:merge-worktree src/module.js --from ../project-feature-branch
# After merge, cleanup is offered automatically
```
