#!/usr/bin/env bash
# Context Engineering Kit - Commands Installer
# 
# Install for Cursor (default, project-level):
#   curl -fsSL https://raw.githubusercontent.com/NeoLabHQ/context-engineering-kit/main/.bin/install-commands.sh | bash
#
# Install for Cursor globally (user-level):
#   curl -fsSL https://raw.githubusercontent.com/NeoLabHQ/context-engineering-kit/main/.bin/install-commands.sh | bash -s -- --global
#
# Install for OpenCode:
#   curl -fsSL https://raw.githubusercontent.com/NeoLabHQ/context-engineering-kit/main/.bin/install-commands.sh | bash -s -- --agent opencode
#
# Install for OpenCode globally:
#   curl -fsSL https://raw.githubusercontent.com/NeoLabHQ/context-engineering-kit/main/.bin/install-commands.sh | bash -s -- --agent opencode --global
#
# This script downloads all plugin commands from the Context Engineering Kit
# and installs them to the appropriate commands directory.

set -euo pipefail

# Configuration
REPO_OWNER="NeoLabHQ"
REPO_NAME="context-engineering-kit"
BRANCH="master"
BASE_URL="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/refs/heads/${BRANCH}"

# Default agent
AGENT="cursor"

# Global installation flag
GLOBAL=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
info() { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Agent configurations
# Format: install_dir:display_name
declare -A AGENT_CONFIG=(
    ["cursor"]=".claude/commands:Cursor" # Cursor uses claude code commands folder by some reason
    ["opencode"]=".opencode/commands:OpenCode"
    ["claude"]=".claude/commands:Claude Code"
    ["windsurf"]=".windsurf/commands:Windsurf"
    ["cline"]=".cline/commands:Cline"
)

# Global agent configurations (user-level installation)
# Format: install_dir:display_name
declare -A AGENT_CONFIG_GLOBAL=(
    ["cursor"]="${HOME}/.cursor/commands:Cursor (global)"
    ["opencode"]="${HOME}/.config/opencode/command:OpenCode (global)"
    ["claude"]="${HOME}/.claude/commands:Claude Code (global)"
    ["windsurf"]="${HOME}/.windsurf/commands:Windsurf (global)"
    ["cline"]="${HOME}/.cline/commands:Cline (global)"
)

# Show help
show_help() {
    echo ""
    echo "Context Engineering Kit - Commands Installer"
    echo ""
    echo "Usage:"
    echo "  curl -fsSL <url> | bash -s -- [OPTIONS]"
    echo "  ./install-commands.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -a, --agent <name>    Target agent/IDE (default: cursor)"
    echo "  -g, --global          Install to user-level directory (e.g., ~/.cursor/commands)"
    echo "  -d, --dir <path>      Custom install directory (overrides --agent and --global)"
    echo "  -l, --list            List available agents"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Supported agents:"
    for agent in "${!AGENT_CONFIG[@]}"; do
        local config="${AGENT_CONFIG[$agent]}"
        local global_config="${AGENT_CONFIG_GLOBAL[$agent]}"
        local dir="${config%%:*}"
        local global_dir="${global_config%%:*}"
        local name="${config#*:}"
        printf "  %-12s → %s (global: %s)\n" "$agent" "$dir" "$global_dir"
    done | sort
    echo ""
    echo "Examples:"
    echo "  # Install for Cursor (default, project-level)"
    echo "  curl -fsSL <url> | bash"
    echo ""
    echo "  # Install for Cursor globally (user-level)"
    echo "  curl -fsSL <url> | bash -s -- --global"
    echo ""
    echo "  # Install for OpenCode globally"
    echo "  curl -fsSL <url> | bash -s -- --agent opencode --global"
    echo ""
    echo "  # Install to custom directory"
    echo "  curl -fsSL <url> | bash -s -- --dir ./my-commands"
    echo ""
}

# List available agents
list_agents() {
    echo ""
    echo "Available agents:"
    echo ""
    # Sort agent names first, then iterate
    local sorted_agents
    sorted_agents=$(printf '%s\n' "${!AGENT_CONFIG[@]}" | sort)
    while IFS= read -r agent; do
        local config="${AGENT_CONFIG[$agent]}"
        local global_config="${AGENT_CONFIG_GLOBAL[$agent]}"
        local dir="${config%%:*}"
        local global_dir="${global_config%%:*}"
        printf "  ${CYAN}%-12s${NC} → %s\n" "$agent" "$dir"
        printf "               --global: %s\n" "$global_dir"
    done <<< "$sorted_agents"
    echo ""
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--agent)
                AGENT="$2"
                shift 2
                ;;
            -g|--global)
                GLOBAL=true
                shift
                ;;
            -d|--dir)
                CUSTOM_DIR="$2"
                shift 2
                ;;
            -l|--list)
                list_agents
                exit 0
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Get install directory for agent
get_install_dir() {
    if [[ -n "${CUSTOM_DIR:-}" ]]; then
        echo "$CUSTOM_DIR"
        return
    fi
    
    if [[ -z "${AGENT_CONFIG[$AGENT]:-}" ]]; then
        error "Unknown agent: $AGENT"
        echo ""
        list_agents
        exit 1
    fi
    
    local config
    if [[ "$GLOBAL" == true ]]; then
        config="${AGENT_CONFIG_GLOBAL[$AGENT]}"
    else
        config="${AGENT_CONFIG[$AGENT]}"
    fi
    echo "${config%%:*}"
}

# Get display name for agent
get_agent_name() {
    if [[ -n "${CUSTOM_DIR:-}" ]]; then
        echo "Custom"
        return
    fi
    
    local config
    if [[ "$GLOBAL" == true ]]; then
        config="${AGENT_CONFIG_GLOBAL[$AGENT]}"
    else
        config="${AGENT_CONFIG[$AGENT]}"
    fi
    echo "${config#*:}"
}

# Plugin definitions with their commands
# Format: plugin_name:command1,command2,command3
PLUGINS=(
    "code-review:review-local-changes,review-pr"
    "customaize-agent:apply-anthropic-skill-best-practices,create-agent,create-command,create-hook,create-skill,create-workflow-command,test-prompt,test-skill"
    "ddd:setup-code-formating"
    "docs:update-docs"
    "fpf:actualize,decay,propose-hypotheses,query,reset,status"
    "git:analyze-issue,attach-review-to-pr,commit,create-pr,load-issues"
    "kaizen:analyse-problem,analyse,cause-and-effect,plan-do-check-act,root-cause-tracing,why"
    "mcp:build-mcp,setup-arxiv-mcp,setup-codemap-cli,setup-context7-mcp,setup-serena-mcp"
    "reflexion:critique,memorize,reflect"
    "sadd:do-competitively,do-in-parallel,do-in-steps,judge-with-debate,judge,launch-sub-agent,tree-of-thoughts"
    "sdd:00-setup,01-specify,02-plan,03-tasks,04-implement,05-document,brainstorm,create-ideas"
    "tdd:fix-tests,write-tests"
    "tech-stack:add-typescript-best-practices"
)

CURSOR_PLUGINS=(
    "customaize-agent:apply-anthropic-skill-best-practices,create-agent,create-command,create-hook,create-skill,create-workflow-command"
    "ddd:setup-code-formating"
    "docs:update-docs"
    "git:analyze-issue,attach-review-to-pr,commit,create-pr,load-issues"
    "kaizen:analyse-problem,analyse,cause-and-effect,plan-do-check-act,root-cause-tracing,why"
    "reflexion:critique,memorize,reflect"
    "tech-stack:add-typescript-best-practices"
)


# Main installation function
install_commands() {
    local install_dir
    local agent_name
    
    install_dir=$(get_install_dir)
    agent_name=$(get_agent_name)
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║       Context Engineering Kit - Commands Installer         ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    info "Target: ${agent_name}"
    
    # Create installation directory
    mkdir -p "$install_dir"
    info "Installing commands to ${install_dir}/"
    echo ""
    
    local total_commands=0
    local installed_commands=0
    local failed_commands=0
    
    # Select plugins array based on agent
    local plugins_to_install
    if [[ "$AGENT" == "cursor" ]]; then
        plugins_to_install=("${CURSOR_PLUGINS[@]}")
    else
        plugins_to_install=("${PLUGINS[@]}")
    fi
    
    for plugin_entry in "${plugins_to_install[@]}"; do
        # Parse plugin name and commands
        local plugin_name="${plugin_entry%%:*}"
        local commands_str="${plugin_entry#*:}"
        
        info "Installing ${plugin_name} commands..."
        
        # Split commands by comma
        IFS=',' read -ra commands <<< "$commands_str"
        
        for cmd in "${commands[@]}"; do
            total_commands=$((total_commands + 1))

            local source_url="${BASE_URL}/plugins/${plugin_name}/commands/${cmd}.md"
            local target_file="${install_dir}/${cmd}.md"
            
            if curl -fsSL "$source_url" -o "$target_file"; then
                success "  ✓ ${plugin_name}:${cmd}"
                installed_commands=$((installed_commands + 1))
            else
                warn "  ✗ ${plugin_name}:${cmd} - failed to download"
                failed_commands=$((failed_commands + 1))
                rm -f "$target_file" || true
            fi
        done
    done
    
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo ""
    success "Installation complete!"
    echo ""
    info "Summary:"
    echo "  • Agent: ${agent_name}"
    echo "  • Commands installed: ${installed_commands}/${total_commands}"
    if [ "$failed_commands" -gt 0 ]; then
        warn "  • Failed: ${failed_commands}"
    fi
    echo "  • Location: ${install_dir}/"
    echo ""
    info "Usage in ${agent_name}:"
    echo "  Type '/' in chat to see available commands"
    echo "  Commands are named: <plugin>-<command>"
    echo "  Example: /code-review-review-pr"
    echo ""
    info "Documentation: https://github.com/${REPO_OWNER}/${REPO_NAME}"
    echo ""
}

# Parse arguments and run
parse_args "$@"
install_commands
