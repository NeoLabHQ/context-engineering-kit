---
name: create-worktree
description: Create and setup git worktrees for parallel development with automatic dependency installation
argument-hint: <name> (e.g., "refactor auth system" or "fix login") or --list to show existing worktrees
model: opus
allowed-tools: Bash(git worktree:*), Bash(git branch:*), Bash(git fetch:*), Bash(git status:*), Bash(ls:*), Bash(pwd:*), Bash(npm install:*), Bash(npm i:*), Bash(yarn install:*), Bash(yarn:*), Bash(pnpm install:*), Bash(pnpm i:*), Bash(bun install:*), Bash(pip install:*), Bash(poetry install:*), Bash(cargo build:*), Bash(go mod download:*)
---

# Claude Command: Create Worktree

Your job is to create and setup git worktrees for parallel development, with automatic detection and installation of project dependencies.

## Instructions

CRITICAL: Perform the following steps exactly as described:

1. **Current state check**: Run `git worktree list` to show existing worktrees and `git status` to verify the repository state is clean (no uncommitted changes that might cause issues)

2. **Fetch latest remote branches**: Run `git fetch --all` to ensure local has knowledge of all remote branches

3. **Parse user input**: Determine what the user wants to create:
   - `<name>`: Create worktree with auto-detected type prefix
   - `--list`: Just show existing worktrees and exit
   - No input: Ask user interactively for the name

4. **Auto-detect branch type from name**: Check if the first word is a known branch type. If yes, use it as the prefix and the rest as the name. If no, default to `feature/`.

   **Known types:** `feature`, `feat`, `fix`, `bug`, `bugfix`, `hotfix`, `release`, `docs`, `test`, `refactor`, `chore`, `spike`, `experiment`, `review`

   **Examples:**
   - `refactor auth system` → `refactor/auth-system`
   - `fix login bug` → `fix/login-bug`
   - `auth system` → `feature/auth-system` (default)
   - `hotfix critical error` → `hotfix/critical-error`

   **Name normalization:** Convert spaces to dashes, lowercase, remove special characters except dashes/underscores

5. **For each worktree to create**:
   a. **Branch name construction**: Build full branch name from detected type and normalized name:
      - `<prefix>/<normalized-name>` (e.g., `feature/auth-system`)

   b. **Branch resolution**: Determine if the branch exists locally, remotely, or needs to be created:
      - If branch exists locally: `git worktree add ../<project>-<name> <branch>`
      - If branch exists remotely (origin/<branch>): `git worktree add --track -b <branch> ../<project>-<name> origin/<branch>`
      - If branch doesn't exist: Ask user for base branch (default: current branch or main/master), then `git worktree add -b <branch> ../<project>-<name> <base>`

   c. **Path convention**: Use sibling directory with pattern `../<project-name>-<name>`
      - Extract project name from current directory
      - Use the normalized name (NOT the full branch with prefix)
      - Example: `feature/auth-system` → `../myproject-auth-system`

   d. **Create the worktree**: Execute the appropriate git worktree add command

   e. **Dependency detection**: Check the new worktree for dependency files and determine if setup is needed:
      - `package.json` -> Node.js project (npm/yarn/pnpm/bun)
      - `requirements.txt` or `pyproject.toml` or `setup.py` -> Python project
      - `Cargo.toml` -> Rust project
      - `go.mod` -> Go project
      - `Gemfile` -> Ruby project
      - `composer.json` -> PHP project

   f. **Package manager detection** (for Node.js projects):
      - `bun.lockb` -> Use `bun install`
      - `pnpm-lock.yaml` -> Use `pnpm install`
      - `yarn.lock` -> Use `yarn install`
      - `package-lock.json` or default -> Use `npm install`

   g. **Automatic setup**: Automatically run dependency installation:
      - cd to worktree and run the detected install command
      - Report progress: "Installing dependencies with [package manager]..."
      - If installation fails, report the error but continue with worktree creation summary

6. **Summary**: Display summary of created worktrees:
   - Worktree path
   - Branch name (full name with prefix)
   - Setup status (dependencies installed or failed)
   - Quick navigation command: `cd <worktree-path>`

## Worktree Path Convention

Worktrees are created as sibling directories to maintain organization:

```
~/projects/
  myproject/                # Main worktree (current directory)
  myproject-add-auth/       # Feature branch worktree (feature/add-auth)
  myproject-critical-bug/   # Hotfix worktree (hotfix/critical-bug)
  myproject-pr-456/         # PR review worktree (review/pr-456)
```

**Naming rules:**

- Pattern: `<project-name>-<name>` (uses the name part, NOT the full branch)
- Branch name: `<type-prefix>/<name>` (e.g., `feature/add-auth`)
- Directory name uses only the `<name>` portion for brevity

## Examples

**Feature worktree (default):**

```bash
> /git:create-worktree auth system
# Branch: feature/auth-system
# Creates: ../myproject-auth-system
```

**Fix worktree:**

```bash
> /git:create-worktree fix login error
# Branch: fix/login-error
# Creates: ../myproject-login-error
```

**Refactor worktree:**

```bash
> /git:create-worktree refactor api layer
# Branch: refactor/api-layer
# Creates: ../myproject-api-layer
```

**Hotfix worktree:**

```bash
> /git:create-worktree hotfix critical bug
# Branch: hotfix/critical-bug
# Creates: ../myproject-critical-bug
```

**List existing worktrees:**

```bash
> /git:create-worktree --list
# Shows: git worktree list output
```

## Setup Detection Examples

**Node.js project with pnpm:**

```
Detected Node.js project with pnpm-lock.yaml
Installing dependencies with pnpm...
✓ Dependencies installed successfully
```

**Python project:**

```
Detected Python project with requirements.txt
Installing dependencies with pip...
✓ Dependencies installed successfully
```

**Rust project:**

```
Detected Rust project with Cargo.toml
Building project with cargo...
✓ Project built successfully
```

## Common Workflows

### Quick Feature Branch

```bash
> /git:create-worktree new dashboard
# Branch: feature/new-dashboard
# Creates worktree, installs dependencies, ready to code
```

### Hotfix While Feature In Progress

```bash
# In main worktree, working on feature
> /git:create-worktree hotfix critical bug
# Branch: hotfix/critical-bug
# Creates separate worktree from main/master
# Fix bug in hotfix worktree
# Return to feature work when done
```

### PR Review Without Stashing

```bash
> /git:create-worktree review pr 123
# Branch: review/pr-123
# Creates worktree for reviewing PR
# Can run tests, inspect code
# Delete when review complete
```

### Experiment or Spike

```bash
> /git:create-worktree spike new architecture
# Branch: spike/new-architecture
# Creates isolated worktree for experimentation
# Discard or merge based on results
```

## Important Notes

- **Branch lock**: Each branch can only be checked out in one worktree at a time. If a branch is already checked out, the command will inform you which worktree has it.

- **Shared .git**: All worktrees share the same Git object database. Changes committed in any worktree are visible to all others.

- **Clean working directory**: The command checks for uncommitted changes and warns if present, as creating worktrees is safest with a clean state.

- **Sibling directories**: Worktrees are always created as sibling directories (using `../`) to keep the workspace organized. Never create worktrees inside the main repository.

- **Automatic dependency installation**: The command automatically detects the project type and package manager, then runs the appropriate install command without prompting.

- **Remote tracking**: For remote branches, worktrees are created with proper tracking setup (`--track` flag) so pulls/pushes work correctly.

## Cleanup

When done with a worktree, use the proper removal command:

```bash
git worktree remove ../myproject-add-auth
```

Or for a worktree with uncommitted changes:

```bash
git worktree remove --force ../myproject-add-auth
```

Never use `rm -rf` to delete worktrees - always use `git worktree remove`.

## Troubleshooting

**"Branch is already checked out"**

- Run `git worktree list` to see where the branch is checked out
- Either work in that worktree or remove it first

**"Cannot create worktree - path already exists"**

- The target directory already exists
- Either remove it or choose a different worktree path

**"Dependency installation failed"**

- Navigate to the worktree manually: `cd ../myproject-<name>`
- Run the install command directly to see full error output
- Common causes: missing system dependencies, network issues, corrupted lockfile

**"Wrong type detected"**

- The first word is used as the branch type if it's a known type
- To force a specific type, start with: `fix`, `hotfix`, `docs`, `test`, `refactor`, `chore`, `spike`, `review`
- Default type is `feature/` when first word isn't a known type
