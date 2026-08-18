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
GITIGNORE_PATTERNS=(".specs/scratchpad/*.md" ".specs/analysis/*.md" ".specs/reports/*.md")

# Create .gitignore if it doesn't exist
if [ ! -f "$GITIGNORE" ]; then
    touch "$GITIGNORE"
fi

# Add each pattern to .gitignore if not already present
for pattern in "${GITIGNORE_PATTERNS[@]}"; do
    if ! grep -qF "$pattern" "$GITIGNORE"; then
        # Ensure the file ends with a newline before appending
        [ -s "$GITIGNORE" ] && [ -z "$(tail -c 1 "$GITIGNORE")" ] || echo "" >> "$GITIGNORE"
        echo "$pattern" >> "$GITIGNORE"
    fi
done

# Create task directories with .gitkeep
mkdir -p "$REPO_ROOT/.specs/tasks/draft"
mkdir -p "$REPO_ROOT/.specs/tasks/todo"
mkdir -p "$REPO_ROOT/.specs/tasks/in-progress"
mkdir -p "$REPO_ROOT/.specs/tasks/done"

touch "$REPO_ROOT/.specs/tasks/draft/.gitkeep"
touch "$REPO_ROOT/.specs/tasks/todo/.gitkeep"
touch "$REPO_ROOT/.specs/tasks/in-progress/.gitkeep"
touch "$REPO_ROOT/.specs/tasks/done/.gitkeep"

# Create sub-tasks directory (tracked in git — sub-task files are spec artifacts, like task files)
mkdir -p "$REPO_ROOT/.specs/sub-tasks"
touch "$REPO_ROOT/.specs/sub-tasks/.gitkeep"

# Create directories (folders tracked via .gitkeep, *.md contents gitignored)
mkdir -p "$REPO_ROOT/.specs/scratchpad"
mkdir -p "$REPO_ROOT/.specs/analysis"
mkdir -p "$REPO_ROOT/.specs/reports"

touch "$REPO_ROOT/.specs/scratchpad/.gitkeep"
touch "$REPO_ROOT/.specs/analysis/.gitkeep"
touch "$REPO_ROOT/.specs/reports/.gitkeep"

# Create skills directory
mkdir -p "$REPO_ROOT/.claude/skills"
touch "$REPO_ROOT/.claude/skills/.gitkeep"

# Output confirmation
echo "Created folders:"
echo "  .specs/tasks/draft/"
echo "  .specs/tasks/todo/"
echo "  .specs/tasks/in-progress/"
echo "  .specs/tasks/done/"
echo "  .specs/sub-tasks/"
echo "  .specs/scratchpad/"
echo "  .specs/analysis/"
echo "  .specs/reports/"
echo "  .claude/skills/"
echo ""
echo "Added to .gitignore: ${GITIGNORE_PATTERNS[*]}"
