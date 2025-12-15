---
name: setup-arxiv-mcp
description: Guide for setup arXiv paper search MCP server using Docker MCP
argument-hint: Optional - specific research topics or paper sources to configure
---

User Input:

```text
$ARGUMENTS
```

# Guide for setup arXiv MCP server via Docker MCP

## 1. Determine setup context

Ask the user where they want to store the configuration:

**Options:**

1. **Project level (shared via git)** - Configuration tracked in version control, shared with team
   - CLAUDE.md updates go to: `./CLAUDE.md`

2. **Project level (personal preferences)** - Configuration stays local, not tracked in git
   - CLAUDE.md updates go to: `./CLAUDE.local.md`
   - Verify these files are listed in `.gitignore`, add them if not

3. **User level (global)** - Configuration applies to all projects for this user
   - CLAUDE.md updates go to: `~/.claude/CLAUDE.md`

Store the user's choice and use the appropriate paths in subsequent steps.

## 2. Check if Docker MCP is available

First, verify that Docker MCP (MCP_DOCKER) is accessible by attempting to use `mcp-find` tool to search for servers.

If Docker MCP is NOT available:

1. Ask user to install Docker Desktop following instructions at: <https://docs.docker.com/desktop/>
2. After Docker Desktop is installed, guide user to connect MCP using: <https://docs.docker.com/ai/mcp-catalog-and-toolkit/get-started/#claude-code>
3. Once configured, ask user to restart Claude Code and run "continue" to resume setup

## 3. Search and add paper-search MCP server

Write to user that regular `arxiv-mcp-server` is known to have issues, specifically is failing to initialize (EOF error during init). So we will use `paper-search` MCP server instead.

Use Docker MCP to find and add the `paper-search` MCP server which provides comprehensive academic paper search capabilities:

```
mcp-find query: "paper-search"
mcp-add name: "paper-search" activate: true
```

This server provides access to multiple academic sources:

- **arXiv** - preprints in physics, mathematics, computer science, etc.
- **PubMed** - biomedical literature
- **bioRxiv/medRxiv** - biology and medicine preprints
- **Semantic Scholar** - AI-powered research tool
- **Google Scholar** - broad academic search
- **IACR** - cryptography research
- **CrossRef** - DOI-based citation database

## 4. Test the setup

Verify the server is working by searching for papers:

```
mcp-exec name: "search_arxiv" arguments: {"query": "test query", "max_results": 2}
```

## 5. Update CLAUDE.md file

Use the path determined in step 1:

Once the paper-search MCP server is successfully set up, update CLAUDE.md file with the following content:

```markdown
### Use Paper Search MCP for Academic Research

Paper Search MCP is available via Docker MCP for searching and downloading academic papers.

**Available tools**:

- `search_arxiv` - Search arXiv preprints (physics, math, CS, etc.)
- `search_pubmed` - Search PubMed biomedical literature
- `search_biorxiv` / `search_medrxiv` - Search biology/medicine preprints
- `search_semantic` - Search Semantic Scholar with year filters
- `search_google_scholar` - Broad academic search
- `search_iacr` - Search cryptography papers
- `search_crossref` - Search by DOI/citation

**Download and read tools**:

- `download_arxiv` / `read_arxiv_paper` - Download/read arXiv PDFs
- `download_biorxiv` / `read_biorxiv_paper` - Download/read bioRxiv PDFs
- `download_semantic` / `read_semantic_paper` - Download/read via Semantic Scholar

**Usage notes**:

- Use `mcp-exec` to call tools, e.g., `mcp-exec name: "search_arxiv" arguments: {"query": "topic", "max_results": 10}`
- Downloaded papers are saved to `./downloads` by default
- For Semantic Scholar, supports multiple ID formats: DOI, ARXIV, PMID, etc.
```

## 6. Alternative: arxiv-mcp-server

If you specifically need the dedicated arXiv MCP server with additional features (deep analysis prompts, local storage management), you can try:

```
mcp-find query: "arxiv"
mcp-config-set server: "arxiv-mcp-server" key: "storage_path" value: "/path/to/papers"
mcp-add name: "arxiv-mcp-server" activate: true
```

Note: This server requires configuration of a storage path for downloaded papers.
