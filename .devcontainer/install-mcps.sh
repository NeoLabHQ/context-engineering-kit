#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Adding Context7 MCP server..."
claude mcp add --scope user --transport http context7 https://mcp.context7.com/mcp --header "CONTEXT7_API_KEY: ${CONTEXT7_API_KEY:-}"

# echo "🔧 Adding Docker MCP servers..."
# docker mcp feature enable profiles 
# docker mcp catalog pull mcp/docker-mcp-catalog
# docker mcp profile create --name dev-tools --server catalog://mcp/docker-mcp-catalog/paper-search --connect claude-code

echo "✅ MCP servers configured."
