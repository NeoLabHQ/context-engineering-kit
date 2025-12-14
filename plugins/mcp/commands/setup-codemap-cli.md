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

## 1. Check if Codemap is already installed

Check whether codemap is installed by running `codemap --version` or `codemap --help`.

If not installed, proceed with setup.

## 2. Load Codemap documentation

Read the following documentation to understand Codemap's capabilities:

- Load <https://raw.githubusercontent.com/JordanCoin/codemap/refs/heads/main/README.md> to understand what Codemap is and its capabilities

## 3. Guide user through installation

### macOS/Linux (Homebrew)

```bash
brew tap JordanCoin/tap && brew install codemap
```

### Windows (Scoop)

```bash
scoop bucket add codemap https://github.com/JordanCoin/scoop-codemap
scoop install codemap
```

## 4. Verify installation

After installation, verify codemap works:

```bash
codemap --version
codemap .
```

## 5. Update CLAUDE.md file

Once Codemap is successfully installed, update CLAUDE.md file with the following content:

```markdown
## Use Codemap CLI for Codebase Navigation

Codemap CLI is available for intelligent codebase visualization and navigation.

### Required Usage

IMPORTANT: Agent MUST run `codemap hook session-start` after forst user input, before any other commands or actions!

- **Working State**: Agent MUST use `codemap --diff --ref master` to research changes different from default branch, and `git diff` + `git status` to research current working state.

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

### Available Hooks

| Command | Trigger | Description |
|---------|---------|-------------|
| `codemap hook session-start` | SessionStart | Full tree, hubs, branch diff, last session context |
| `codemap hook pre-edit` | PreToolUse (Edit\|Write) | Who imports file + what hubs it imports |
| `codemap hook post-edit` | PostToolUse (Edit\|Write) | Impact of changes (same as pre-edit) |
| `codemap hook prompt-submit` | UserPromptSubmit | Hub context for mentioned files + session progress |
| `codemap hook pre-compact` | PreCompact | Saves hub state to .codemap/hubs.txt |
| `codemap hook session-stop` | SessionEnd | Edit timeline with line counts and stats |

```

if the default branch is not `main`, but instead `master` (or something else) update content accordingly:
 - use `codemap --diff --ref master` instead of regular `codemap --diff`
 - use `codemap hook session-start --ref=master` instead of regular `codemap hook session-start`

## 6. Update .gitignore file

Update .gitignore file to include `.codemap/` directory:

```text
.codemap/
```

## 7. Test Codemap

Run a quick test to verify everything works:

```bash
codemap .
codemap --diff
```

