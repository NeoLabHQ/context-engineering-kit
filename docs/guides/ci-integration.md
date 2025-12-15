# CI/CD Integration

Automate code reviews on every pull request using GitHub Actions with the Code Review plugin. It automatically determines complexity of the changes and launches appropriate number of agents to review them without loosing context. Balances the speed and quality of the review.

## When to Use

- Automate code review on every PR without manual invocation
- Enforce consistent code quality standards across the team
- Catch bugs, security issues, and quality problems before human review
- Reduce review burden on senior developers

## GitHub Actions Setup

### Step 1: Configure Secrets

Run the following command in Claude Code to set up the required GitHub App and secrets:

```bash
/install-github-app
```

This creates the `CLAUDE_CODE_OAUTH_TOKEN` secret in your repository settings and adds `claude-code-review.yml` workflow file to your repository.

### Step 2: Create Workflow File

Update `.github/workflows/claude-code-review.yml` with following content:

```yaml
name: Claude Code Review

on:
  pull_request:
    types:
    - opened
    - synchronize # remove if want to run only when PR is opened
    # Uncomment to limit which files can trigger the workflow
    # paths:
    #   - "**/*.ts"
    #   - "**/*.tsx"
    #   - "**/*.js"
    #   - "**/*.jsx"
    #   - "**/*.py"
    #   - "**/*.sql"
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

## How It Works

More info how review works: [PR Review Guide](./pr-review.md)

Short summary:

1. **Trigger**: Workflow runs on PR open and synchronize events
2. **Analysis**: Claude uses six specialized agents to review the PR:
   - Bug Hunter - Identifies potential bugs and edge cases
   - Security Auditor - Finds security vulnerabilities
   - Test Coverage Reviewer - Evaluates test coverage
   - Code Quality Reviewer - Assesses code structure
   - Contracts Reviewer - Reviews API contracts
   - Historical Context Reviewer - Analyzes codebase patterns
3. **Report**: Findings are posted as PR comments organized by severity
4. **Updates**: Sticky comments update on new commits instead of creating duplicates
