# MCP Plugin - Usage Examples

Real-world scenarios demonstrating effective use of the MCP plugin for documentation access, semantic code analysis, and custom MCP server development.

## Examples

### Setting Up Documentation for a New Project

**Scenario**: You're starting a new Next.js project with Prisma and want up-to-date documentation access from the start.

```bash
# Set up the project
> npx create-next-app@latest my-app

# Install the MCP plugin
> /plugin install mcp@NeoLabHQ/context-engineering-kit

# Configure documentation access
> /mcp:setup-context7-mcp nextjs 14, prisma, typescript, zod
```

**Expected Flow**:

1. Command checks if Context7 MCP is already configured
2. If not, guides you through installation for your environment
3. Searches Context7 for documentation IDs for each technology
4. Updates CLAUDE.md with recommended library IDs

**Result in CLAUDE.md**:

```markdown
### Use Context7 MCP for Loading Documentation

Context7 MCP is available to fetch up-to-date documentation with code examples.

**Recommended library IDs**:

- `nextjs` - Next.js 14 documentation with App Router
- `prisma` - Prisma ORM schema and client documentation
- `typescript` - TypeScript language reference
- `zod` - Zod schema validation library
```

**Using the Documentation**:

After setup, when you ask about Next.js Server Actions or Prisma relations, the LLM queries Context7 for current documentation instead of relying on potentially outdated training data.

---

### Auto-Detecting Project Technologies

**Scenario**: You've inherited a project and want to set up documentation access without manually listing all dependencies.

```bash
# Navigate to project
> cd existing-project

# Let the command analyze your project
> /mcp:setup-context7-mcp
```

**Expected Flow**:

1. Command scans `package.json`, `requirements.txt`, or other dependency files
2. Identifies React, Redux, Express, and PostgreSQL
3. Searches Context7 for matching documentation
4. Updates CLAUDE.md with discovered technologies

**When Analysis Finds Technologies**:

```
Analyzed project structure:
- Found package.json with React 18, Redux Toolkit, Express
- Found docker-compose.yml with PostgreSQL
- Detected TypeScript configuration

Setting up documentation for: react, @reduxjs/toolkit, express, postgresql, typescript
```

---

### Setting Up Codebase Visualization with Codemap

**Scenario**: You want to visualize your codebase structure, track changes, and enable AI-assisted navigation hooks.

```bash
# Set up Codemap CLI for codebase visualization
> /mcp:setup-codemap-cli
```

**Expected Flow**:

1. Command checks if Codemap is already installed via `codemap --version`
2. If not installed, detects your OS and provides installation instructions
3. Fetches latest Codemap documentation from GitHub
4. Guides through installation (Homebrew for macOS/Linux, Scoop for Windows)
5. Verifies installation with test commands
6. Updates CLAUDE.md with usage instructions and hook configuration
7. Adds `.codemap/` to .gitignore

**Setup Interaction**:

```
Checking Codemap installation...
- codemap: Not found

Detected OS: Linux

Installation instructions:
  brew tap JordanCoin/tap && brew install codemap

Run the above command and then continue.
```

**After Successful Setup**:

```
Codemap CLI is now installed!

Testing:
- codemap --version: 0.1.0
- codemap .: Working

Updated CLAUDE.md with Codemap usage instructions.
Updated .gitignore with .codemap/ directory.
```

**Using Codemap**:

```bash
# Visualize project structure
> codemap .

# See what changed vs main branch
> codemap --diff --ref master

# Understand dependencies
> codemap --deps .

# Filter by file type
> codemap --only ts,tsx .
```

---

### Setting Up Semantic Code Analysis for a Large Codebase

**Scenario**: You're working on a large monorepo and need better code navigation than grep can provide.

```bash
# Set up Serena for semantic analysis
> /mcp:setup-serena-mcp
```

**Expected Flow**:

1. Command checks for Serena availability
2. Verifies `uv` is installed
3. Detects your MCP client (Claude Code in this case)
4. Guides through configuration if needed
5. Initializes project indexing
6. Updates CLAUDE.md with usage guidelines

**Setup Interaction**:

```
Checking Serena MCP availability...
- Serena tools not accessible

Prerequisites check:
- uv: Installed (0.4.18)

Detected client: Claude Code

Configuration needed:
1. Add Serena to your MCP configuration
2. Restart Claude to load the new MCP server

After restart, run: /mcp:setup-serena-mcp continue
```

**After Successful Setup**:

```
Serena MCP is now configured!

Running project indexing...
- Indexed 1,247 files
- Found 8,432 symbols

Testing connection:
- find_symbol: Working
- list_symbols: Working
- read_file: Working

Updated CLAUDE.md with Serena usage guidelines.
```

**Using Semantic Operations**:

```bash
# Find a specific function across the codebase
> "Find all usages of the validateUser function"

# Serena uses semantic search instead of text grep
# Returns: function definition, all call sites, and type information
```

---

### Combining Context7 and Serena for Maximum Effectiveness

**Scenario**: You want both documentation access and semantic code understanding for a complex project.

```bash
# First, set up documentation access
> /mcp:setup-context7-mcp react, graphql, @apollo/client

# Then, set up semantic code analysis
> /mcp:setup-serena-mcp
```

**Result in CLAUDE.md**:

```markdown
### Use Context7 MCP for Loading Documentation

Context7 MCP is available to fetch up-to-date documentation with code examples.

**Recommended library IDs**:

- `react` - React 18 documentation
- `graphql` - GraphQL specification and best practices
- `@apollo/client` - Apollo Client documentation

### Use Serena MCP for Semantic Code Analysis

Serena MCP is available for advanced code retrieval and editing capabilities.

- Use Serena's tools for precise code manipulation in structured codebases
- Prefer symbol-based operations over file-based grep/sed operations

Key usage points:
- Use `find_symbol` to locate functions, classes, and types by name
- Use `list_symbols` to explore available symbols in a file or module
- Prefer semantic operations for refactoring over text replacement
```

**Workflow Benefits**:

1. When implementing a new GraphQL resolver, Context7 provides current Apollo Client patterns
2. When refactoring, Serena finds all symbol usages across the codebase
3. Both tools work together: documentation for "how to do it", semantic analysis for "where to do it"

---

### Setting Up Academic Paper Search via Docker MCP

**Scenario**: You're conducting research and need to search and read academic papers from arXiv, Semantic Scholar, and other sources.

```bash
# Set up paper search MCP via Docker MCP
> /mcp:setup-arxiv-mcp
```

**Expected Flow**:

1. Command checks if Docker MCP is available
2. If not, guides you through Docker Desktop installation
3. Searches for and adds `paper-search` MCP server from Docker catalog
4. Activates the server's tools in your session
5. Tests the connection with a sample search
6. Updates CLAUDE.md with usage instructions

**Setup Interaction**:

```
Checking Docker MCP availability...

Note: The standard arxiv-mcp-server has known initialization issues.
Using paper-search MCP server instead, which provides access to multiple academic sources.

Adding paper-search MCP server...
mcp-find query: "paper-search"
mcp-add name: "paper-search" activate: true

Testing connection...
search_arxiv query: "test" max_results: 2

Paper Search MCP is now configured!
```

**Using Paper Search**:

```bash
# Search arXiv for machine learning papers
> mcp-exec name: "search_arxiv" arguments: {"query": "transformer attention mechanism", "max_results": 10}

# Search Semantic Scholar with year filter
> mcp-exec name: "search_semantic" arguments: {"query": "large language models", "year": "2023-", "max_results": 5}

# Search cryptography papers
> mcp-exec name: "search_iacr" arguments: {"query": "zero knowledge proofs", "max_results": 5}

# Download and read a specific paper
> mcp-exec name: "read_arxiv_paper" arguments: {"paper_id": "2106.12345"}

# Search by DOI via CrossRef
> mcp-exec name: "get_crossref_paper_by_doi" arguments: {"doi": "10.1038/nature12373"}
```

**Available Sources**:

| Tool | Source | Best For |
|------|--------|----------|
| `search_arxiv` | arXiv | Physics, Math, CS preprints |
| `search_pubmed` | PubMed | Biomedical literature |
| `search_semantic` | Semantic Scholar | AI-powered search with year filters |
| `search_biorxiv` | bioRxiv | Biology preprints |
| `search_medrxiv` | medRxiv | Medical preprints |
| `search_iacr` | IACR ePrint | Cryptography research |
| `search_crossref` | CrossRef | DOI-based citation metadata |
| `search_google_scholar` | Google Scholar | Broad academic search |

---

### Building a Custom MCP Server for Slack Integration

**Scenario**: Your team uses Slack extensively and you want the LLM to interact with Slack channels and messages.

```bash
# Start the MCP server development guide
> /mcp:build-mcp

# When prompted, describe your use case:
> "I want to build an MCP server that lets the LLM read and post messages
   to Slack channels, search message history, and manage channel membership"
```

**Phase 1 Output - Research and Planning**:

```markdown
## Implementation Plan: Slack MCP Server

### Tool Selection (Priority Order)

1. **search_messages** - Search across channels with filters
   - High value: Enables finding relevant context quickly
   - Workflow: Single tool replaces manual channel browsing

2. **post_message** - Send messages to channels
   - Essential for communication workflows
   - Include thread support for context

3. **list_channels** - Get available channels
   - Foundation for other operations
   - Support filtering by membership/type

4. **get_channel_history** - Read recent messages
   - Support for pagination
   - Include thread expansion option

5. **manage_channel_membership** - Join/leave channels
   - Lower priority but enables autonomy

### Input/Output Design

- Use "concise" vs "detailed" response formats
- Limit message returns to 25 by default
- Support pagination for longer histories
- Return human-readable timestamps, not Unix epochs
```

**Phase 2 - Implementation Example**:

```python
# slack_mcp_server.py (generated with guidance)
from mcp import Server, Tool
from pydantic import BaseModel, Field

class SearchMessagesInput(BaseModel):
    """Search parameters for Slack messages."""
    query: str = Field(
        description="Search query. Supports Slack search operators.",
        examples=["from:@alice deployment", "in:#engineering bug"]
    )
    channels: list[str] | None = Field(
        default=None,
        description="Limit search to specific channels. Omit to search all."
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum messages to return. Default 10 for context efficiency."
    )
    format: str = Field(
        default="concise",
        pattern="^(concise|detailed)$",
        description="concise: message + author + timestamp. detailed: includes reactions, threads."
    )

@server.tool
async def search_messages(params: SearchMessagesInput) -> str:
    """
    Search Slack messages across channels.

    Use this tool to find relevant conversations, decisions, or context.
    Returns messages sorted by relevance with author and timestamp.

    Example queries:
    - "deployment friday" - Find messages about Friday deployments
    - "from:@alice in:#engineering" - Alice's messages in #engineering
    - "has:reaction" - Messages with reactions (indicates importance)

    For actionable results, combine with post_message to respond in context.
    """
    # Implementation...
```

**Phase 4 - Evaluation Questions**:

```xml
<evaluation>
  <qa_pair>
    <question>Search for messages containing "deployment" in the #engineering channel from the last week. Who posted the most recent one?</question>
    <answer>alice</answer>
  </qa_pair>
  <qa_pair>
    <question>Find the channel with the most members that discusses backend topics. What is its name?</question>
    <answer>backend-general</answer>
  </qa_pair>
</evaluation>
```

---

### Building a Python MCP Server for Internal API

**Scenario**: Your company has an internal API for managing customer data and you want LLM access.

```bash
> /mcp:build-mcp

> "Build an MCP server for our internal Customer API at https://api.internal.com
   I need to search customers, view customer details, and update customer status"
```

**Design Principles Applied**:

```markdown
## Tool Design for Customer API

### Workflow-Oriented Design

**Instead of**:
- get_customer_by_id
- get_customer_by_email
- get_customer_by_name

**We build**:
- search_customers (handles all lookup methods with smart defaults)

### Context-Optimized Responses

**Instead of**:
```json
{
  "id": "cust_123",
  "created_at": 1699574400,
  "updated_at": 1699660800,
  "metadata": {...},
  "billing_info": {...},
  ...100 more fields
}
```

**We return**:
```
Customer: John Doe (cust_123)
Email: john@example.com
Status: Active | Since: Nov 2024
Recent Activity: 3 orders in last 30 days

[Use format="detailed" for full record]
```

### Actionable Errors

**Instead of**:
```
Error: 404 Not Found
```

**We return**:
```
Customer not found with ID 'cust_123'.
Try:
- search_customers with email or name
- Check if ID format is correct (should be 'cust_' prefix)
```
```

---

### Using MCP in a Feature Development Workflow

**Scenario**: Complete feature development using MCP servers alongside other plugins.

```bash
# Set up MCP servers at project start
> /mcp:setup-context7-mcp react, typescript, prisma
> /mcp:setup-serena-mcp

# Research phase - Context7 provides current documentation
> /sdd:01-research

# Implementation - Serena helps navigate codebase
> /sdd:04-implement

# Review with semantic understanding
> /reflexion:critique

# Save learnings
> /reflexion:memorize
```

**How MCP Enhances Each Phase**:

| Phase | MCP Contribution |
|-------|------------------|
| Research | Context7 provides current API documentation |
| Implementation | Serena finds related code and symbols |
| Review | Serena enables precise code navigation during critique |
| Documentation | Context7 ensures examples match current APIs |

---

### Troubleshooting: Context7 Documentation Not Found

**Scenario**: Context7 cannot find documentation for a library you need.

```bash
> /mcp:setup-context7-mcp obscure-library

# Response:
# Documentation not found for: obscure-library
#
# Suggestions:
# 1. Check library name spelling
# 2. Try alternative names (e.g., 'react-query' vs '@tanstack/react-query')
# 3. Library may not be indexed - consider contributing to Context7
# 4. Use WebFetch to load documentation directly from library repository
```

**Workaround**:

```bash
# Manually add documentation source to CLAUDE.md
> "Add a note to CLAUDE.md that for obscure-library documentation,
   load from https://github.com/org/obscure-library/blob/main/docs/api.md"
```

---

### Troubleshooting: Serena Indexing Failures

**Scenario**: Serena fails to index your project correctly.

```bash
> /mcp:setup-serena-mcp

# Issue: Indexing failed for src/generated/*
# These files are auto-generated and should be excluded
```

**Resolution**:

```bash
# Configure Serena to exclude generated files
> "Configure Serena to exclude the src/generated directory from indexing"

# Re-run indexing
> /mcp:setup-serena-mcp

# Result:
# Indexing complete:
# - Excluded: src/generated/* (1,234 files)
# - Indexed: 456 files
# - Found: 2,341 symbols
```

## Integration with Other Plugins

### With Reflexion

```bash
# Set up documentation, then verify configuration
> /mcp:setup-context7-mcp react, nextjs
> /reflexion:reflect

# After building a custom MCP server, get comprehensive review
> /mcp:build-mcp
> /reflexion:critique
> /reflexion:memorize "MCP server design patterns"
```

### With SDD (Spec-Driven Development)

```bash
# Documentation access improves research quality
> /mcp:setup-context7-mcp
> /sdd:01-research

# Semantic analysis helps implementation
> /mcp:setup-serena-mcp
> /sdd:04-implement
```

### With TDD

```bash
# Semantic analysis helps find test targets
> /mcp:setup-serena-mcp
> /tdd:write-tests
```

### With Kaizen

```bash
# Semantic analysis aids root cause investigation
> /mcp:setup-serena-mcp
> /kaizen:why "Why is the authentication failing?"

# Codemap visualizes codebase for root cause tracing
> /mcp:setup-codemap-cli
> /kaizen:root-cause-tracing
```

### With Feature Development Workflow

```bash
# Set up complete MCP tooling for a new project
> /mcp:setup-context7-mcp react, typescript, prisma
> /mcp:setup-serena-mcp
> /mcp:setup-codemap-cli

# Now Claude has:
# - Up-to-date documentation access (Context7)
# - Semantic code navigation (Serena)
# - Codebase visualization and change tracking (Codemap)
```
