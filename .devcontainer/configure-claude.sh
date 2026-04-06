#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Configuring Claude Code environment..."

# -- Copy statusline script to ~/.claude --
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p ~/.claude
cp "$SCRIPT_DIR/statusline.sh" ~/.claude/statusline.sh
chmod +x ~/.claude/statusline.sh
echo "✅ Copied statusline.sh to ~/.claude/"

if [ ! -f ~/.claude/settings.json ]; then
  echo "🔧 Creating ~/.claude/settings.json..."
  cat > ~/.claude/settings.json << 'EOF'
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo 'git diff:' && git diff --stat && echo 'git status:' && git status"
          }
        ]
      }
    ]
  },
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline.sh"
  },
  "alwaysThinkingEnabled": true,
  "skipDangerousModePermissionPrompt": true,
  "effortLevel": "high",
  "autoUpdatesChannel": "stable",
  "companyAnnouncements": ["Thank you for using NeoLab Dev Container Sandbox", "Happy engineering!"]
}
EOF
  echo "✅ Created ~/.claude/settings.json with bypass permissions."
fi

if [ ! -f ~/.claude.json ]; then
  echo "🔧 Creating ~/.claude.json..."
  cat > ~/.claude.json << 'EOF'
{
  "autoCompactEnabled": false
}
EOF
  echo "✅ Created ~/.claude.json with autoCompactEnabled set to false."
fi

retry() {
  local max_attempts="${RETRY_ATTEMPTS:-3}"
  local delay="${RETRY_DELAY:-1}"
  local attempt=1
  while [ "$attempt" -le "$max_attempts" ]; do
    if "$@"; then
      return 0
    fi
    echo "⚠️ Attempt $attempt/$max_attempts failed: $*"
    if [ "$attempt" -lt "$max_attempts" ]; then
      echo "   Retrying in ${delay}s..."
      sleep "$delay"
    fi
    attempt=$((attempt + 1))
  done
  echo "❌ All $max_attempts attempts failed: $*"
  return 1
}

# echo "🔧 Installing typescript lsp..."

retry claude plugin marketplace add anthropics/claude-plugins-official
retry claude plugin install typescript-lsp@claude-plugins-official

# echo "🔧 Installing context-engineering-kit plugins..."

retry claude plugin marketplace add NeoLabHQ/context-engineering-kit
retry claude plugin install sdd@context-engineering-kit
retry claude plugin install sadd@context-engineering-kit
retry claude plugin install git@context-engineering-kit


echo "🚀 Claude Code environment ready."
echo "Use 'claude' to run Claude Code"