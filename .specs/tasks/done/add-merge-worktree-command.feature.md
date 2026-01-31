---
title: Add merge-worktree command to git plugin
depends_on:
  - add-create-worktree-command.feature.md
  - add-compare-worktrees-command.feature.md
---

## Initial User Prompt

add merge-worktree command in git plugin. It should support: merging of signgle file or directory from worktree, chery-picking commit from worktree, merging from multiple worktrees in the current branch, picking which changes from each to merge. Including: Selective File Checkout, Interactive Patch Selection, Cherry-Pick with No-Commit + Reset, Manual Merge with Conflicts. Also after command execution it should ask whether user want to remove worktrees to clean local state.

Important: before implmeneting command need read ./plugins/git/skills/worktrees/SKILL.md file and understand how worktrees work.

## Description

// Will be filled in future stages by business analyst
