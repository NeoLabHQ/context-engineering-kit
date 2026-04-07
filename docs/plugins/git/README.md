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

## Commands

- [/git:commit](./commit.md) - Create well-formatted commits with conventional commit messages and emoji.
- [/git:create-pr](./create-pr.md) - Create pull requests using GitHub CLI with proper templates and formatting.
- [/git:analyze-issue](./analyze-issue.md) - Analyze a GitHub issue and create a detailed technical specification.
- [/git:load-issues](./load-issues.md) - Load all open issues from GitHub and save them as markdown files.
- [/git:attach-review-to-pr](./attach-review-to-pr.md) - Add line-specific review comments to pull requests using GitHub CLI API.
- [/git:create-worktree](./create-worktree.md) - Create and setup git worktrees for parallel development with automatic dependency installation.
- [/git:compare-worktrees](./compare-worktrees.md) - Compare files and directories between git worktrees or worktree and current branch.
- [/git:merge-worktree](./merge-worktree.md) - Merge changes from worktrees into current branch with selective file checkout, cherry-picking, interactive patch selection, or manual merge.

## Skills

- [git-worktrees](./git-worktrees.md) - Skill for Parallel Branch Development in same file system using git worktrees.
- [git-notes](./git-notes.md) - Skill about using git notes to add metadata to commits without changing history.

