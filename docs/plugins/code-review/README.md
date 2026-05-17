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

## CI/CD Integration

You can intergreate this plugin with your CI/CD pipeline by using Offical Anthropics Claude Code Action. See [CI/CD Integration](../../guides/ci-integration.md) for more details.

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


## Commands

- [/code-review:review-local-changes](./review-local-changes.md) - Local Changes Review
- [/code-review:review-pr](./review-pr.md) - Pull Request Review

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
    - ready_for_review
    - reopened
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

          prompt: '/code-review:review-pr ${{ github.repository }}/pull/${{ github.event.pull_request.number }} Note: The PR branch is already checked out in the current working directory.'

          # Skill and Bash(gh pr comment:*) is required for review, the rest is optional, but recommended for better context and quality of the review.
          claude_args: '--allowed-tools "Skill,Bash,Glob,Grep,Read,Task,mcp__github_inline_comment__create_inline_comment,Bash(gh issue view:*),Bash(gh search:*),Bash(gh issue list:*),Bash(gh pr comment:*),Bash(gh pr edit:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(gh pr list:*),Bash(gh api:*)"'
```

## Output Formats

### Local Changes Review (`review-local-changes`)

Produces a structured report organized by severity:

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

### PR Review (`review-pr`)

Posts inline comments directly on PR lines - no overall report. Each comment follows this format:

```markdown
🔴/🟠/🟡 [Critical/High/Medium]: [Brief description]

[Evidence: What was observed and consequence if unfixed]

```suggestion
[code fix if applicable]
```
```

