#!/bin/bash
# create-folders.sh - Create task folder structure and add scratchpad to gitignore

set -e

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Not a git repository" >&2
    exit 1
fi

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
GITIGNORE="$REPO_ROOT/.gitignore"
SCRATCHPAD_PATTERN=".specs/scratchpad/"

# Create .gitignore if it doesn't exist
if [ ! -f "$GITIGNORE" ]; then
    touch "$GITIGNORE"
fi

# Check if .specs/scratchpad/ is in .gitignore
if ! grep -qF "$SCRATCHPAD_PATTERN" "$GITIGNORE"; then
    # Ensure the file ends with a newline before appending
    [ -s "$GITIGNORE" ] && [ -z "$(tail -c 1 "$GITIGNORE")" ] || echo "" >> "$GITIGNORE"
    echo "$SCRATCHPAD_PATTERN" >> "$GITIGNORE"
fi

# Create task directories with .gitkeep
mkdir -p "$REPO_ROOT/.specs/tasks/draft"
mkdir -p "$REPO_ROOT/.specs/tasks/todo"
mkdir -p "$REPO_ROOT/.specs/tasks/in-progress"
mkdir -p "$REPO_ROOT/.specs/tasks/done"

touch "$REPO_ROOT/.specs/tasks/draft/.gitkeep"
touch "$REPO_ROOT/.specs/tasks/todo/.gitkeep"
touch "$REPO_ROOT/.specs/tasks/in-progress/.gitkeep"
touch "$REPO_ROOT/.specs/tasks/done/.gitkeep"
touch "$REPO_ROOT/.specs/tasks/reports/.gitkeep"

# Create scratchpad directory (no .gitkeep - folder is gitignored)
mkdir -p "$REPO_ROOT/.specs/scratchpad"

# Create analysis directory
mkdir -p "$REPO_ROOT/.specs/analysis"
touch "$REPO_ROOT/.specs/analysis/.gitkeep"

# Create skills directory
mkdir -p "$REPO_ROOT/.claude/skills"
touch "$REPO_ROOT/.claude/skills/.gitkeep"

# Output confirmation
echo "Created folders:"
echo "  .specs/tasks/draft/"
echo "  .specs/tasks/todo/"
echo "  .specs/tasks/in-progress/"
echo "  .specs/tasks/done/"
echo "  .specs/scratchpad/"
echo "  .specs/analysis/"
echo "  .claude/skills/"
echo ""
echo "Added to .gitignore: $SCRATCHPAD_PATTERN"
