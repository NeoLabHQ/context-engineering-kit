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
> /commit

# Create a pull request
> /create-pr
```

#### Analyze Open GitHub issues

```bash
# Load all open issues
> /load-issues

# Analyze a GitHub issue
> /analyze-issue 123
```

[Usage Examples](./usage-examples.md)

## Commands

- [/commit](./commit.md) - Create well-formatted commits with conventional commit messages and emoji.
- [/create-pr](./create-pr.md) - Create pull requests using GitHub CLI with proper templates and formatting.
- [/analyze-issue](./analyze-issue.md) - Analyze a GitHub issue and create a detailed technical specification.
- [/load-issues](./load-issues.md) - Load all open issues from GitHub and save them as markdown files.
- [/attach-review-to-pr](./attach-review-to-pr.md) - Add line-specific review comments to pull requests using GitHub CLI API.
- [/worktrees](./git-worktrees.md) - Create, compare, and merge git worktrees for parallel development with automatic dependency installation

## Skills

- [notes](./git-notes.md) - Skill about using git notes to add metadata to commits without changing history.

