---
description: Bump changed plugin and marketplace version
argument-hint: minor|major|patch (version increment type)
allowed-tools: Bash(just set-version*), Bash(just set-marketplace-version*), Bash(git diff:*), Bash(git status:*)
---

# Bump Plugin Version

Detect changed plugins and bump their versions along with the marketplace version.

## Current State

- Git status: !`git status --short`
- Changed files in plugins: !`git diff --name-only HEAD | grep "^plugins/" | cut -d'/' -f2 | sort -u`

## Instructions

1. **Parse the argument**: `$ARGUMENTS` should be one of: `minor`, `major`, or `patch`
   - If no argument provided or invalid, ask the user to specify: minor, major, or patch

2. **Identify changed plugins** from the git diff output above
   - Look for changes in `plugins/<plugin-name>/` directories
   - Extract unique plugin names

3. **For each changed plugin**:
   - Read current version from `plugins/<plugin-name>/.claude-plugin/plugin.json`
   - Calculate new version based on increment type:
     - `patch`: 1.0.0 → 1.0.1
     - `minor`: 1.0.0 → 1.1.0
     - `major`: 1.0.0 → 2.0.0
   - Run: `just set-version <name> <new-version>`

4. **Bump marketplace version** using the same increment type:
   - Read current version from `.claude-plugin/marketplace.json`
   - Calculate new version
   - Run: `just set-marketplace-version <new-version>`

5. **Report** what was bumped:
   - List each plugin with old → new version
   - Show marketplace old → new version