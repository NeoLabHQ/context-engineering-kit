# Enhancing Project File Structure Context

Improve AI assistant understanding of your codebase through intelligent project visualization and automatic context injection.

## When to Use

- Setting up a new project for AI-assisted development
- Working with large codebases where navigation is challenging
- Wanting automatic context about project structure in every session
- Tracking changes across branches during development
- Debugging issues that span multiple files or modules

## Why File Structure Context Matters

AI assistants work best when they understand the full picture of your codebase. Without proper context:

- **Navigation becomes guesswork** - The AI may search inefficiently or miss relevant files
- **Changes lack awareness** - The AI doesn't know what you've been working on
- **Architecture decisions suffer** - Without seeing the big picture, suggestions may not fit
- **Context gets wasted** - Manually explaining project structure uses valuable tokens

With proper file structure context:

- **Instant project awareness** - AI sees your entire codebase structure at session start
- **Change tracking** - AI knows exactly what files have been modified vs main branch
- **Smart navigation** - Dependency analysis helps understand module relationships
- **Efficient sessions** - No need to repeatedly explain project layout

## Plugins Needed

- [MCP](../plugins/mcp/README.md) - For Codemap CLI setup

## Workflow

### How It Works

```
┌─────────────────────────────────────────────┐
│ 1. Install Codemap CLI                      │
│    (codebase visualization tool)            │
└────────────────────┬────────────────────────┘
                     │
                     │ provides tree, diff, and dependency commands
                     ▼
┌─────────────────────────────────────────────┐
│ 2. Configure Session Hooks                  │
│    (.claude/settings.json)                  │
└────────────────────┬────────────────────────┘
                     │
                     │ automatic context on session start
                     ▼
┌─────────────────────────────────────────────┐
│ 3. Update CLAUDE.md                         │
│    (usage instructions for AI)              │
└────────────────────┬────────────────────────┘
                     │
                     │ AI knows how to use these tools
                     ▼
┌─────────────────────────────────────────────┐
│ 4. Every Session Gets Context               │
│    (automatic project awareness)            │
└─────────────────────────────────────────────┘
```

### 1. Install Codemap CLI

Use the `/mcp:setup-codemap-cli` command to install and configure Codemap:

```bash
/mcp:setup-codemap-cli
```

This command will:
1. Check if Codemap is already installed
2. Provide OS-specific installation instructions (Homebrew for macOS/Linux, Scoop for Windows)
3. Verify installation works
4. Update CLAUDE.md with usage instructions
5. Configure hooks in `.claude/settings.json`
6. Add `.codemap/` to .gitignore

### 2. Understanding What Gets Configured

After running the setup command, you'll have:

**CLAUDE.md additions:**

```markdown
## Use Codemap CLI for Codebase Navigation

Codemap CLI is available for intelligent codebase visualization and navigation.

**Required Usage** - You MUST use `codemap --diff --ref master` to research
changes different from default branch, and `git diff` + `git status` to
research current working state.

### Quick Start

codemap .                    # Project tree
codemap --only md .          # Just Markdown files
codemap --diff --ref master  # What changed vs master
codemap --deps .             # Dependency flow
```

**Session hooks in `.claude/settings.json`:**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "codemap hook session-start && echo 'git diff:' && git diff --stat && echo 'git status:' && git status"
          }
        ]
      }
    ]
  }
}
```

### 3. What Context You Get

At the start of every Claude Code session, the hooks automatically provide:

| Context Type | Description | Example Use |
|--------------|-------------|-------------|
| **Project Tree** | Full codebase structure with file sizes and types | Understanding project layout |
| **Hub Files** | Key files that many others depend on | Identifying critical modules |
| **Branch Diff** | Files changed vs main branch | Knowing what you're working on |
| **Git Status** | Current working state (staged, unstaged, untracked) | Seeing uncommitted changes |

### 4. Using Codemap Commands

Once configured, you can use these commands anytime:

```bash
# Full project tree
codemap .

# Filter by file type
codemap --only ts,tsx .
codemap --only md .

# Exclude patterns
codemap --exclude .png,node_modules .

# Limit depth for large projects
codemap --depth 2 .

# See what changed vs main branch
codemap --diff --ref master
codemap --diff --ref develop

# Analyze dependencies
codemap --deps .

# Check who imports a specific file
codemap --importers src/utils/auth.ts

# City skyline visualization
codemap --skyline .
```

## Advanced Configuration

### Adding More Hooks

The setup command will ask if you want additional hooks. Available options:

| Hook | Trigger | What It Provides |
|------|---------|------------------|
| `codemap hook session-start` | SessionStart | Full tree, hubs, branch diff, last session context |
| `codemap hook pre-edit` | PreToolUse (Edit\|Write) | Who imports file + what hubs it imports |
| `codemap hook post-edit` | PostToolUse (Edit\|Write) | Impact of changes (same as pre-edit) |
| `codemap hook prompt-submit` | UserPromptSubmit | Hub context for mentioned files + session progress |
| `codemap hook pre-compact` | PreCompact | Saves hub state to .codemap/hubs.txt |
| `codemap hook session-stop` | SessionEnd | Edit timeline with line counts and stats |

**Full hooks configuration example:**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "codemap hook session-start"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "codemap hook pre-edit"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "codemap hook post-edit"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "codemap hook prompt-submit"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "codemap hook pre-compact"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "codemap hook session-stop"
          }
        ]
      }
    ]
  }
}
```

### Custom Branch Reference

If your main branch is `master` instead of `main`, update the hooks:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "codemap hook session-start --ref=master"
          }
        ]
      }
    ]
  }
}
```

### Combining with Git Status

For comprehensive working state awareness, combine Codemap with git commands:

```json
{
  "hooks": {
    "session-start": "codemap hook session-start && echo 'git diff:' && git diff --stat && echo 'git status:' && git status"
  }
}
```

This provides:
- Project structure and hub files (from Codemap)
- Branch diff summary (from Codemap)
- Uncommitted changes summary (from git diff)
- Full working tree status (from git status)

## What You Get

After completing this setup, every Claude Code session will automatically have:

- **Project tree** - Full visualization of your codebase structure
- **Hub awareness** - Knowledge of key files that many others depend on
- **Change context** - Understanding of what's been modified vs main branch
- **Working state** - Visibility into staged, unstaged, and untracked changes

This context enables the AI to:
- Navigate efficiently without repeated exploration
- Make suggestions that fit your architecture
- Understand the scope of your current work
- Provide relevant file references in responses

## Best Practices

1. **Start sessions with context** - The SessionStart hook ensures AI has project awareness from the first message

2. **Use diff for focused work** - When working on a feature branch, `codemap --diff` shows exactly what's changed

3. **Leverage dependency analysis** - Before refactoring, use `codemap --deps` to understand impact

4. **Filter large projects** - Use `--only`, `--exclude`, and `--depth` to focus on relevant areas

5. **Check importers before changes** - Use `codemap --importers <file>` to see what might break

6. **Commit .claude/settings.json** - Share hooks configuration with your team for consistent AI experience
