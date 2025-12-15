---
name: setup-codemap-cli
description: Guide for setup Codemap CLI for intelligent codebase visualization and navigation
argument-hint: Optional - specific configuration preferences or OS type
---

User Input:

```text
$ARGUMENTS
```

# Guide for setup Codemap CLI

## 1. Determine setup context

Ask the user where they want to store the configuration:

**Options:**

1. **Project level (shared via git)** - Configuration tracked in version control, shared with team
   - CLAUDE.md updates go to: `./CLAUDE.md`
   - Hook settings go to: `./.claude/settings.json`

2. **Project level (personal preferences)** - Configuration stays local, not tracked in git
   - CLAUDE.md updates go to: `./CLAUDE.local.md`
   - Hook settings go to: `./.claude/settings.local.json`
   - Verify these files are listed in `.gitignore`, add them if not

3. **User level (global)** - Configuration applies to all projects for this user
   - CLAUDE.md updates go to: `~/.claude/CLAUDE.md`
   - Hook settings go to: `~/.claude/settings.json`

Store the user's choice and use the appropriate paths in subsequent steps.

## 2. Check if Codemap is already installed

Check whether codemap is installed by running `codemap --version` or `codemap --help`.

If not installed, proceed with setup.

## 3. Load Codemap documentation

Read the following documentation to understand Codemap's capabilities:

- Load <https://raw.githubusercontent.com/JordanCoin/codemap/refs/heads/main/README.md> to understand what Codemap is and its capabilities

## 4. Guide user through installation

### macOS/Linux (Homebrew)

```bash
brew tap JordanCoin/tap && brew install codemap
```

### Windows (Scoop)

```bash
scoop bucket add codemap https://github.com/JordanCoin/scoop-codemap
scoop install codemap
```

## 5. Verify installation

After installation, verify codemap works:

```bash
codemap --version
codemap .
```

## 6. Update CLAUDE.md file

Use the path determined in step 1. Once Codemap is successfully installed, update the appropriate CLAUDE.md file with the following content:

```markdown
## Use Codemap CLI for Codebase Navigation

Codemap CLI is available for intelligent codebase visualization and navigation.

**Required Usage** - You MUST use `codemap --diff --ref master` to research changes different from default branch, and `git diff` + `git status` to research current working state.

### Quick Start

```bash
codemap .                    # Project tree
codemap --only swift .       # Just Swift files
codemap --exclude .xcassets,Fonts,.png .  # Hide assets
codemap --depth 2 .          # Limit depth
codemap --diff               # What changed vs main
codemap --deps .             # Dependency flow
```

### Options

| Flag | Description |
|------|-------------|
| `--depth, -d <n>` | Limit tree depth (0 = unlimited) |
| `--only <exts>` | Only show files with these extensions |
| `--exclude <patterns>` | Exclude files matching patterns |
| `--diff` | Show files changed vs main branch |
| `--ref <branch>` | Branch to compare against (with --diff) |
| `--deps` | Dependency flow mode |
| `--importers <file>` | Check who imports a file |
| `--skyline` | City skyline visualization |
| `--json` | Output JSON |

**Smart pattern matching** - no quotes needed:
- `.png` - any `.png` file
- `Fonts` - any `/Fonts/` directory
- `*Test*` - glob pattern

### Diff Mode

See what you're working on:

```bash
codemap --diff
codemap --diff --ref develop
```

```

if the default branch is not `main`, but instead `master` (or something else) update content accordingly:
 - use `codemap --diff --ref master` instead of regular `codemap --diff`


## 7. Update .gitignore file

Update .gitignore file to include `.codemap/` directory:

```text
.codemap/
```

## 8. Test Codemap

Run a quick test to verify everything works:

```bash
codemap .
codemap --diff
```

## 9. Add hooks to settings file

- Use the settings path determined in step 1. Create the settings file if it doesn't exist and add the following content:

    ```json
    {
        "hooks": {
            "session-start": "codemap hook session-start && echo 'git diff:' && git diff --stat && echo 'git status:' && git status"
        }
    }
    ```

    if default branch is not `main`, but instead `master` (or something else) update content accordingly:
    - use `codemap hook session-start --ref=master` instead of regular `codemap hook session-start`
    - For rest of commands also add `--ref=master` flag.

- Ask user whether he want to add any other hooks and provide list of options with descriptions. Add hooks that he asks for.

### Available Hooks

| Command | Trigger | Description |
|---------|---------|-------------|
| `codemap hook session-start` | SessionStart | Full tree, hubs, branch diff, last session context |
| `codemap hook pre-edit` | PreToolUse (Edit\|Write) | Who imports file + what hubs it imports |
| `codemap hook post-edit` | PostToolUse (Edit\|Write) | Impact of changes (same as pre-edit) |
| `codemap hook prompt-submit` | UserPromptSubmit | Hub context for mentioned files + session progress |
| `codemap hook pre-compact` | PreCompact | Saves hub state to .codemap/hubs.txt |
| `codemap hook session-stop` | SessionEnd | Edit timeline with line counts and stats |


### Example of file with full hooks configuration

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