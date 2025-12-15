# Code Review Plugin

Comprehensive multi-agent code review system that examines code from multiple specialized perspectives to catch bugs, security issues, and quality problems before they reach production.

## Focused on

- **Multi-perspective analysis** - Six specialized agents examine code from different angles
- **Early bug detection** - Catch bugs before commits and pull requests
- **Security auditing** - Identify vulnerabilities and attack vectors
- **Quality enforcement** - Maintain code standards and best practices

## Overview

The Code Review plugin implements a multi-agent code review system where specialized AI agents examine code from different perspectives. Six agents work in parallel: Bug Hunter, Security Auditor, Test Coverage Reviewer, Code Quality Reviewer, Contracts Reviewer, and Historical Context Reviewer. This provides comprehensive, professional-grade code review before commits or pull requests.

## Quick Start

```bash
# Install the plugin
/plugin install code-review@NeoLabHQ/context-engineering-kit

# Review uncommitted local changes
> /code-review:review-local-changes

# Review a pull request
> /code-review:review-pr #123
```

[Usage Examples](./usage-examples.md)

## Agent Architecture

```
Code Review Command
        │
        ├──> Bug Hunter (parallel)
        ├──> Security Auditor (parallel)
        ├──> Test Coverage Reviewer (parallel)
        ├──> Code Quality Reviewer (parallel)
        ├──> Contracts Reviewer (parallel)
        └──> Historical Context Reviewer (parallel)
                │
                ▼
        Aggregated Report
```


## Commands Overview

### /code-review:review-local-changes - Local Changes Review

Review uncommitted local changes using all specialized agents with code improvement suggestions.

- Purpose - Comprehensive review before committing
- Output - Structured report with findings by severity

```bash
/code-review:review-local-changes ["review-aspects"]
```

#### Arguments

Optional review aspects to focus on (e.g., "security", "bugs", "tests")

#### How It Works

1. **Change Detection**: Identifies all uncommitted changes in the working directory
   - Staged changes
   - Unstaged modifications
   - New files

2. **Parallel Agent Analysis**: Spawns six specialized agents simultaneously
   - Bug Hunter - Identifies potential bugs and edge cases
   - Security Auditor - Finds security vulnerabilities
   - Test Coverage Reviewer - Evaluates test coverage
   - Code Quality Reviewer - Assesses code structure
   - Contracts Reviewer - Reviews API contracts
   - Historical Context Reviewer - Analyzes codebase patterns

3. **Finding Aggregation**: Combines all agent reports
   - Categorizes by severity (Critical, High, Medium, Low)
   - Removes duplicates
   - Adds file and line references

4. **Report Generation**: Produces actionable report with prioritized findings

#### Usage Examples

```bash
# Review all local changes
> /code-review:review-local-changes

# Focus on security aspects
> /code-review:review-local-changes security

# After implementing a feature
> claude "implement user authentication"
> /code-review:review-local-changes
```

#### Best Practices

- Review before committing - Run review on local changes before `git commit`
- Address critical issues first - Fix Critical and High priority findings immediately
- Iterate after fixes - Run again to verify issues are resolved
- Combine with reflexion - Use `/reflexion:memorize` to save patterns for future reference

### /code-review:review-pr - Pull Request Review

Comprehensive pull request review using all specialized agents.

- Purpose - Review PR changes before merge
- Output - Detailed findings with line-specific comments

```bash
/code-review:review-pr ["PR number or review-aspects"]
```

#### Arguments

PR number (e.g., #123, 123) and/or review aspects to focus on

#### How It Works

1. **PR Context Loading**: Fetches PR details and diff
   - Changed files
   - Commit messages
   - PR description
   - Base branch context

2. **Parallel Agent Analysis**: Same six agents analyze the PR diff
   - Each agent examines changes from their specialty perspective
   - Considers PR context and commit messages

3. **Finding Aggregation**: Combines findings with PR-specific context
   - Links findings to specific lines in the diff
   - Considers breaking changes and backward compatibility

4. **Report Generation**: Produces PR-ready report
   - Structured for easy review
   - Action items for the PR author

#### Usage Examples

```bash
# Review PR by number
> /code-review:review-pr #123

# Review PR with focus on security
> /code-review:review-pr #123 security

# Review current branch's PR
> /code-review:review-pr
```

#### Best Practices

- Review before requesting human review - Address automated findings first
- Share report with team - Include findings in PR comments
- Track patterns - Use findings to improve coding guidelines
- Don't ignore low priority - Create issues for future improvement

## Review Agents

### Bug Hunter

**Focus**: Identifies potential bugs and edge cases through root cause analysis

**What it catches:**
- Null pointer exceptions
- Off-by-one errors
- Race conditions
- Memory and resource leaks
- Unhandled error cases
- Logic errors

### Security Auditor

**Focus**: Security vulnerabilities and attack vectors

**What it catches:**
- SQL injection risks
- XSS vulnerabilities
- CSRF missing protection
- Authentication/authorization bypasses
- Exposed secrets or credentials
- Insecure cryptography usage

### Test Coverage Reviewer

**Focus**: Test quality and coverage

**What it evaluates:**
- Test coverage gaps
- Missing edge case tests
- Integration test needs
- Test quality and meaningfulness

### Code Quality Reviewer

**Focus**: Code structure and maintainability

**What it evaluates:**
- Code complexity
- Naming conventions
- Code duplication
- Design patterns usage
- Code smells

### Contracts Reviewer

**Focus**: API contracts and interfaces

**What it reviews:**
- API endpoint definitions
- Request/response schemas
- Breaking changes
- Backward compatibility
- Type safety

### Historical Context Reviewer

**Focus**: Changes relative to codebase history

**What it analyzes:**
- Consistency with existing patterns
- Previous bug patterns
- Architectural drift
- Technical debt indicators

## CI/CD Integration

### GitHub Actions

You can use [anthropics/claude-code-action](https://github.com/marketplace/actions/claude-code-action-official) to run this plugin for PR reviews in github actions.

1. Use `/install-github-app` command to setup workflow and secrets.
2. Set content of `.github/workflows/claude-code-review.yml` to the following:

```yaml
name: Claude Code Review

on:
  pull_request:
    types: 
    - opened
    - synchronize # remove if want to run only, when PR is opened
    # Uncomment to limit which files can trigger the workflow
    # paths:
    #   - "**/*.ts"
    #   - "**/*.tsx"
    #   - "**/*.js"
    #   - "**/*.jsx"
    #   - "**/*.py"
    #   - "**/*.sql"
    #   - "**/*.SQL"
    #   - "**/*.sh"

jobs:
  claude-review:
    name: Claude Code Review
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: write
      id-token: write
      actions: read

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1
      
      - name: Run Claude Code Review
        id: claude-review
        uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          track_progress: true # attach tracking comment
          use_sticky_comment: true

          plugin_marketplaces: https://github.com/NeoLabHQ/context-engineering-kit.git
          plugins: "code-review@context-engineering-kit\ngit@context-engineering-kit\ntdd@context-engineering-kit\nsadd@context-engineering-kit\nddd@context-engineering-kit\nsdd@context-engineering-kit\nkaizen@context-engineering-kit"
          
          prompt: |
            REPO: ${{ github.repository }}
            PR NUMBER: ${{ github.event.pull_request.number }}

            CRITICAL: You MUST use SlashCommand tool to read and perform /code-review:review-pr command EXACTLY!
            Do not analyze or read PR, code or anything else UNTIL you have read the command!

            Note: The PR branch is already checked out in the current working directory.
          
          # SlashCommand and Bash(gh pr comment:*) is required for review, the rest is optional, but recommended for better context and quality of the review.
          claude_args: '--allowed-tools "SlashCommand,Bash,Glob,Grep,Read,Task,mcp__github_inline_comment__create_inline_comment,Bash(gh issue view:*),Bash(gh search:*),Bash(gh issue list:*),Bash(gh pr comment:*),Bash(gh pr edit:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(gh pr list:*),Bash(gh api:*)"'
```

## Report Structure

Reviews produce structured output organized by severity:

```markdown
# Code Review Report

## Executive Summary
[Overview of changes and quality assessment]

## Critical Issues (Must Fix)
- [Issue with location and suggested fix]

## High Priority (Should Fix)
- [Issue with location and suggested fix]

## Medium Priority (Consider Fixing)
- [Issue with location]

## Low Priority (Nice to Have)
- [Issue with location]

## Action Items
- [ ] Critical action 1
- [ ] High priority action 1
```
