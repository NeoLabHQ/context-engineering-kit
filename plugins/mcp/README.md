# MCP Plugin

Commands for integrating Model Context Protocol (MCP) servers with your AI-powered development workflow. Set up well-known MCP servers and create custom servers to extend LLM capabilities.

## Plugin Target

Simplify integration of MCP servers into your development workflow.

## Overview

The MCP (Model Context Protocol) plugin helps you integrate MCP servers into your development environment. MCP is an open protocol that enables AI assistants to interact with external services, databases, and tools through a standardized interface.

This plugin provides five key commands:

1. **Context7 MCP Setup** - Access up-to-date documentation for any library or framework
2. **Serena MCP Setup** - Enable semantic code analysis and symbol-based operations
3. **Codemap CLI Setup** - Enable intelligent codebase visualization and navigation
4. **arXiv/Paper Search MCP Setup** - Search and download academic papers from multiple sources
5. **Build MCP** - Create custom MCP servers for any service or API

Each setup command supports configuration at multiple levels:

- **Project level (shared)** - Configuration tracked in git, shared with team via `./CLAUDE.md`
- **Project level (personal)** - Local configuration in `./CLAUDE.local.md`, not tracked in git
- **User level (global)** - Configuration in `~/.claude/CLAUDE.md`, applies to all projects

The command guides through the MCP setup process and updates the appropriate CLAUDE.md file based on your choice to ensure consistent MCP usage.

## Quick Start

Open Claude Code in your project directory and run the following commands to setup MCP servers.

```bash
# Install the plugin
/plugin install mcp@NeoLabHQ/context-engineering-kit

# Set up documentation access for your project
> /mcp:setup-context7-mcp react, typescript, prisma

# Enable semantic code analysis
> /mcp:setup-serena-mcp

# Set up codebase visualization
> /mcp:setup-codemap-cli
```

[Usage Examples](./usage-examples.md)

## Commands Overview

### /mcp:setup-context7-mcp - Documentation Access

Set up Context7 MCP server to provide real-time access to library and framework documentation, eliminating hallucinations from outdated training data.

- Purpose - Configure documentation access for your project's technology stack
- Output - Working Context7 integration with CLAUDE.md configuration

```bash
/mcp:setup-context7-mcp [technologies]
```

#### What is Context7?

Context7 is an MCP server that fetches up-to-date documentation with code examples for any library or framework. Instead of relying on potentially outdated training data, the LLM can query actual documentation in real-time.

Benefits:
- Access latest API references and code examples
- Eliminate hallucinations about deprecated methods or incorrect signatures
- Get version-specific documentation for your exact dependencies
- Reduce back-and-forth when the LLM suggests outdated patterns

#### Arguments

Optional list of languages and frameworks to configure documentation for. If omitted, the command analyzes your project structure to identify relevant technologies.

Examples:
- `react, typescript, prisma` - Specific technologies
- `nextjs 14, tailwind` - Version-specific documentation
- (no arguments) - Auto-detect from project files

#### How It Works

1. **Availability Check**: Verifies if Context7 MCP server is already configured
2. **Setup Guidance**: If not available, guides you through the installation process for your operating system and development environment
3. **Technology Analysis**: Parses your input or scans project structure to identify relevant documentation
4. **Documentation Search**: Queries Context7 to find available documentation IDs for your technologies
5. **CLAUDE.md Update**: Adds recommended library IDs and usage instructions to your project configuration

#### Usage Examples

```bash
# Configure for a React/TypeScript project
> /mcp:setup-context7-mcp react, typescript, @tanstack/react-query

# Let the command detect technologies from your project
> /mcp:setup-context7-mcp

# Specific framework versions
> /mcp:setup-context7-mcp nextjs 14, prisma 5, zod
```

After setup, your CLAUDE.md will include:

```markdown
### Use Context7 MCP for Loading Documentation

Context7 MCP is available to fetch up-to-date documentation with code examples.

**Recommended library IDs**:

- `react` - React core library documentation
- `typescript` - TypeScript language reference
- `prisma` - Prisma ORM documentation
```

#### Best Practices

- Run early in project setup to establish documentation access from the start
- Include specific versions when working with rapidly evolving libraries
- Review the generated documentation IDs and remove any that are not relevant
- Re-run when adding new major dependencies to your project

---

### /mcp:setup-serena-mcp - Semantic Code Analysis

Set up Serena MCP server for semantic code retrieval and symbol-based editing capabilities, enabling precise code manipulation in large codebases.

- Purpose - Enable intelligent code navigation and manipulation
- Output - Configured Serena integration with indexed project

```bash
/mcp:setup-serena-mcp [configuration preferences]
```

#### What is Serena?

Serena is an MCP server that provides semantic understanding of your codebase. Unlike text-based search (grep), Serena understands code structure - functions, classes, types, and their relationships.

Benefits:
- Find symbols by meaning, not just text matching
- Navigate complex codebases with symbol-based operations
- Make precise code changes without breaking references
- Understand code relationships and dependencies
- Refactor with confidence using semantic operations

#### Arguments

Optional configuration preferences or client type. The command adapts its setup guidance based on your development environment (Claude Code, Claude Desktop, Cursor, VSCode, etc.).

#### How It Works

1. **Availability Check**: Tests if Serena tools (`find_symbol`, `list_symbols`) are accessible
2. **Documentation Loading**: Fetches latest Serena documentation for setup guidance
3. **Prerequisites Verification**: Confirms `uv` is installed (required for running Serena)
4. **Client Configuration**: Provides setup instructions specific to your MCP client
5. **Project Setup**: Guides through project initialization and indexing
6. **Connection Test**: Verifies Serena tools are working correctly
7. **CLAUDE.md Update**: Adds semantic code analysis guidelines to your project

#### Usage Examples

```bash
# Standard setup with auto-detection
> /mcp:setup-serena-mcp

# Specify your client
> /mcp:setup-serena-mcp cursor

# With specific configuration needs
> /mcp:setup-serena-mcp claude-desktop
```

After setup, your CLAUDE.md will include:

```markdown
### Use Serena MCP for Semantic Code Analysis

Serena MCP is available for advanced code retrieval and editing capabilities.

- Use Serena's tools for precise code manipulation in structured codebases
- Prefer symbol-based operations over file-based grep/sed operations

Key usage points:
- Use `find_symbol` to locate functions, classes, and types by name
- Use `list_symbols` to explore available symbols in a file or module
- Prefer semantic operations for refactoring over text replacement
```

#### Best Practices

- Set up Serena for large codebases where text search becomes unwieldy
- Use semantic operations for refactoring to ensure all references are updated
- Re-index the project after major structural changes
- Combine with Context7 for documentation + code understanding
- Prefer symbol-based navigation over grep for code exploration

---

### /mcp:setup-codemap-cli - Codebase Visualization

Set up Codemap CLI for intelligent codebase visualization and navigation, providing tree views, dependency analysis, and change tracking.

- Purpose - Enable comprehensive codebase understanding and navigation
- Output - Working Codemap installation with CLAUDE.md configuration

```bash
/mcp:setup-codemap-cli [OS type or configuration preferences]
```

#### What is Codemap?

Codemap is a CLI tool that provides intelligent codebase visualization and navigation. It generates tree views, tracks changes, analyzes dependencies, and integrates with Claude Code through hooks.

Benefits:
- Visualize project structure with smart filtering
- Track changes vs main branch at a glance
- Analyze file dependencies and import relationships
- Integrate with Claude Code through session hooks
- Generate city skyline visualizations of codebase

#### Arguments

Optional OS type or configuration preferences. The command auto-detects your operating system and provides appropriate installation instructions.

Examples:
- (no arguments) - Auto-detect OS and install
- `macos` - macOS-specific instructions
- `windows` - Windows-specific instructions

#### How It Works

1. **Installation Check**: Verifies if Codemap is already installed via `codemap --version`
2. **Documentation Loading**: Fetches latest Codemap documentation from GitHub
3. **Installation Guidance**: Provides OS-specific installation commands (Homebrew for macOS/Linux, Scoop for Windows)
4. **Verification**: Tests installation with basic commands
5. **CLAUDE.md Update**: Adds Codemap usage instructions and hook configuration
6. **.gitignore Update**: Adds `.codemap/` directory to ignore list

#### Usage Examples

```bash
# Standard setup with auto-detection
> /mcp:setup-codemap-cli

# Specify your OS
> /mcp:setup-codemap-cli macos
> /mcp:setup-codemap-cli windows
```

After setup, your CLAUDE.md will include:

```markdown
## Use Codemap CLI for Codebase Navigation

Codemap CLI is available for intelligent codebase visualization and navigation.

**Required Usage** - You MUST use `codemap --diff --ref master` to research changes different from default branch, and `git diff` + `git status` to research current working state.

### Quick Start

codemap .                    # Project tree
codemap --only md .          # Just Markdown files
codemap --diff --ref master  # What changed vs master
codemap --deps .             # Dependency flow
```

The command also configures Claude Code hooks in `.claude/settings.json` for automatic session context.

#### Best Practices

- Run at project start to establish codebase understanding
- Use hooks to maintain context during long coding sessions
- Combine `--diff` with `--ref` to compare against your main branch
- Use `--deps` to understand module relationships before refactoring
- Exclude generated files and assets with `--exclude` for cleaner output

---

### /mcp:setup-arxiv-mcp - Academic Paper Search

Set up the Paper Search MCP server via Docker MCP for searching and downloading academic papers from multiple sources including arXiv, PubMed, Semantic Scholar, and more.

- Purpose - Enable academic paper search and retrieval for research workflows
- Output - Working Paper Search MCP integration with CLAUDE.md configuration

```bash
/mcp:setup-arxiv-mcp [research topics or configuration]
```

#### What is Paper Search MCP?

Paper Search MCP is a Docker-based MCP server that provides comprehensive access to academic literature. It aggregates search across multiple academic sources and enables downloading and reading papers directly.

Benefits:
- Search papers across arXiv, PubMed, bioRxiv, medRxiv, Semantic Scholar, and more
- Download PDFs and extract text content for analysis
- Filter by year, author, and other metadata
- Access cryptography papers via IACR
- Cross-reference with DOI via CrossRef

#### Arguments

Optional research topics or specific paper sources to configure. The command will guide you through Docker MCP setup if not already available.

Examples:
- (no arguments) - Standard setup with all paper sources
- `machine learning, transformers` - Mention specific research areas
- `cryptography` - Focus on specific domain

#### Prerequisites

- **Docker Desktop** - Required for Docker MCP integration
- **Docker MCP Toolkit** - For managing MCP servers via Docker

#### How It Works

1. **Docker MCP Check**: Verifies Docker MCP is available
2. **Server Search**: Finds and adds `paper-search` MCP server from Docker catalog
3. **Activation**: Enables the server's tools in your session
4. **Connection Test**: Verifies search functionality works
5. **CLAUDE.md Update**: Adds paper search usage instructions

#### Available Tools

**Search Tools**:
- `search_arxiv` - Search arXiv preprints (physics, math, CS, etc.)
- `search_pubmed` - Search PubMed biomedical literature
- `search_biorxiv` / `search_medrxiv` - Search biology/medicine preprints
- `search_semantic` - Search Semantic Scholar with year filters
- `search_google_scholar` - Broad academic search
- `search_iacr` - Search cryptography papers (IACR ePrint)
- `search_crossref` - Search by DOI/citation metadata

**Download and Read Tools**:
- `download_arxiv` / `read_arxiv_paper` - Download/read arXiv PDFs
- `download_biorxiv` / `read_biorxiv_paper` - Download/read bioRxiv PDFs
- `download_semantic` / `read_semantic_paper` - Download/read via Semantic Scholar

#### Usage Examples

```bash
# Standard setup
> /mcp:setup-arxiv-mcp

# After setup, search for papers
> read transformer attention mechanism paper

# Search Semantic Scholar with year filter
> search large language models papers from 2023

# Download and read a paper
> read paper 2106.12345
```

After setup, your CLAUDE.md will include:

---

### /mcp:build-mcp - Custom MCP Server Development

Comprehensive guide for creating high-quality MCP servers that enable LLMs to interact with external services through well-designed tools.

- Purpose - Build custom MCP servers for any service or API
- Output - Production-ready MCP server with tools and evaluations

```bash
/mcp:build-mcp
```

#### When to Build Custom MCP Servers

Build an MCP server when you need the LLM to:
- Interact with internal company APIs or services
- Access databases or data sources not available via existing MCP servers
- Integrate with third-party services (CRMs, project management, communication tools)
- Perform specialized operations unique to your domain

#### How It Works

The command guides you through a four-phase development process:

**Phase 1: Deep Research and Planning**

1. **Agent-Centric Design Principles**
   - Build workflow tools, not just API wrappers
   - Optimize for limited context windows
   - Design actionable error messages
   - Follow natural task subdivisions

2. **Protocol Study**: Load MCP specification from `modelcontextprotocol.io`

3. **Framework Selection**:
   - Python with FastMCP for rapid development
   - TypeScript with MCP SDK for type safety

4. **API Research**: Exhaustively study the target API documentation

5. **Implementation Planning**:
   - Tool selection and prioritization
   - Shared utilities design
   - Input/output schema design
   - Error handling strategy

**Phase 2: Implementation**

1. **Project Structure**: Set up according to language-specific best practices
2. **Core Infrastructure**: Build shared utilities first (API helpers, error handling, formatting)
3. **Tool Implementation**: Systematically implement each planned tool
4. **Annotations**: Add proper tool hints (readOnly, destructive, idempotent)

**Phase 3: Review and Refine**

1. **Code Quality Review**: DRY principle, composability, consistency
2. **Testing**: Verify syntax and imports (note: MCP servers are long-running, use evaluation harness)
3. **Quality Checklist**: Language-specific verification

**Phase 4: Create Evaluations**

1. **Tool Inspection**: Understand available capabilities
2. **Content Exploration**: Use read-only operations to explore data
3. **Question Generation**: Create 10 complex, realistic evaluation questions
4. **Answer Verification**: Verify each answer is correct and stable

#### Usage Examples

```bash
# Start building an MCP server
> /mcp:build-mcp

# The command will guide you through:
# 1. Understanding your integration requirements
# 2. Choosing Python or TypeScript
# 3. Designing tools for your use case
# 4. Implementing with best practices
# 5. Testing and evaluation
```
