# Recommended MCP Servers

Model Context Protocol (MCP) servers extend Claude Code's capabilities by providing access to external tools, data sources, and specialized functionality. This page documents MCP servers that complement Context Engineering Kit plugins and enhance your development workflow.

## What is MCP?

Model Context Protocol is a standard for connecting LLMs to external data sources and tools. MCP servers expose:

- **Resources** - External data that Claude can read (files, documentation, APIs)
- **Tools** - Actions Claude can execute (search, transform, create)
- **Prompts** - Reusable prompt templates with dynamic inputs

For complete MCP documentation, see [modelcontextprotocol.io](https://modelcontextprotocol.io/).

## Why Use MCP with CEK?

Context Engineering Kit focuses on improving Claude's reasoning and workflow patterns. MCP servers complement this by:

- **Extending knowledge** - Access to external documentation and data
- **Providing tools** - Specialized operations beyond Claude's native capabilities
- **Reducing context pollution** - Fetch only needed information on demand
- **Enabling specialization** - Domain-specific tools and knowledge

## Recommended Servers

- [Context7](https://github.com/upstash/context7) - Load documentation for specific technologies, frameworks, and libraries directly into Claude's context. Setup using `/mcp:setup-context7-mcp` command.
- [Serena](https://github.com/oraios/serena) - Semantic code retrieval and intelligent editing capabilities using vector embeddings. Setup using `/mcp:setup-serena-mcp` command.
- [Paper Search](https://hub.docker.com/extensions/mcp/paper-search) - Search and download academic papers from arXiv, PubMed, Semantic Scholar, bioRxiv, and more via Docker MCP. Setup using `/mcp:setup-arxiv-mcp` command.
- [Perplexity](https://github.com/perplexityai/modelcontextprotocol) - Enhanced search and research capabilities with access to real-time information and web resources. 
