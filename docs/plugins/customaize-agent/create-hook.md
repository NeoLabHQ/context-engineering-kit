# /create-hook - Claude Code Hook Configuration

Create and configure Claude Code lifecycle hooks with intelligent project analysis, suggestions, and automated testing. Automate workflows like code formatting, validation, security checks, and notifications by running scripts when Claude edits files, executes commands, or needs user input.

- Purpose - Create and configure hooks that run when Claude Code edits files, executes commands, or needs user input.
- Output - Working hook script registered in Claude Code settings

```bash
/create-hook ["hook type or description"]
```

## Arguments

Optional hook type or description of desired behavior (e.g., "type-check on after editing", "prevent commiting to main branch").

## Usage Examples

```bash
# Create a TypeScript type-checking hook (runs after Claude edits .ts files)
> /create-hook type-check TypeScript files

# Create a security scanning hook (blocks dangerous Bash commands)
> /create-hook prevent dangerous shell commands

# Create auto-formatting hook (runs Prettier after file edits)
> /create-hook auto-format with Prettier

# Let the assistant analyze project and suggest hooks
> /create-hook
```

## How It Works

1. **Environment Analysis**: Detects project tooling automatically
   - TypeScript (`tsconfig.json`) → Suggests type-checking hooks
   - Prettier (`.prettierrc`) → Suggests auto-formatting hooks
   - ESLint (`.eslintrc.*`) → Suggests linting hooks
   - Package scripts → Suggests test/build validation hooks
   - Git repository → Suggests security scanning hooks

2. **Hook Configuration**: Asks targeted questions about Claude Code hook behavior
   - What should this hook do?
   - **When should it run?** Claude Code lifecycle events:
     - `PreToolUse` - Before tool execution (can block)
     - `PostToolUse` - After tool succeeds (feedback/fixes)
     - `UserPromptSubmit` - Before processing user input
     - `SessionStart`, `Stop`, `Notification`, etc.
   - **Which tools trigger it?** `Write`, `Edit`, `Bash`, `*` (all tools)
   - **Scope?** `global` (~/.claude/), `project` (.claude/), `project-local` (.claude/settings.local.json)
   - **Should Claude see and fix issues?** (use `additionalContext` for errors)
   - **Should successful operations be silent?** (use `suppressOutput: true`)

3. **Hook Creation**: Generates complete Claude Code hook setup
   - Script in `~/.claude/hooks/` or `.claude/hooks/` with executable permissions
   - Registration in appropriate `settings.json` (`~/.claude/settings.json` or `.claude/settings.json`)
   - Project-specific commands using detected tooling (TypeScript, Prettier, ESLint)
   - Proper JSON input/output format for Claude Code communication

4. **Testing & Validation**: Tests both happy and sad paths
   - **Happy path**: Create conditions where hook should pass (valid code, formatted files, safe commands)
   - **Sad path**: Create conditions where hook should fail/warn (type errors, unformatted code, dangerous operations)
   - **Verification**: Check if hook blocks/warns/provides context as intended

## Claude Code Hook Events

These hooks run at specific points in Claude Code's lifecycle, not git's lifecycle:

| Hook Event | When It Fires | Use Case |
|------------|---------------|----------|
| **PostToolUse** | After tool succeeds | Code formatting, linting, type-checking, automated fixes |
| **PreToolUse** | Before tool executes (can block) | Security validation, block dangerous commands, enforce policies |
| **UserPromptSubmit** | Before processing user input | Add context, validate prompts, enforce constraints |
| **SessionStart** | Session begins/resumes | Load dev context, set environment variables |
| **Stop** | Claude finishes responding | Verify all tasks complete, run final checks |
| **Notification** | Claude needs attention | Desktop notifications, alerts |

## Best Practices

- **Test both paths** - Always verify both success and failure scenarios
- **Use absolute paths** - Avoid relative paths in scripts, use `$CLAUDE_PROJECT_DIR` to reference project root
- **Read JSON from stdin** - Claude Code passes hook input as JSON via stdin (never use argv)
- **Use exit codes correctly**:
  - `exit 0` = success/allow operation
  - `exit 2` = block operation (PreToolUse) or provide critical feedback
  - Other codes = non-blocking errors
- **Provide specific feedback** - Use `additionalContext` in JSON output for Claude to see and fix issues
- **Keep success silent** - Use `suppressOutput: true` in JSON output to avoid context pollution
- **Output valid JSON** - When returning structured decisions, exit 0 and print JSON to stdout (not stderr)
