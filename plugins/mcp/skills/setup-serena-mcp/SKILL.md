---
name: setup-serena-mcp
description: Guide for setup Serena MCP server for semantic code retrieval and editing capabilities
argument-hint: Optional - specific configuration preferences or client type
---

User Input:

```text
$ARGUMENTS
```

# Guide for setup Serena MCP server

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

## 2. Check if Serena MCP server is already setup

Check whether you have access to Serena MCP server by attempting to use one of its tools (e.g., `find_symbol` or `get_symbols_overview`).

If no access, proceed with setup.

## 3. Load Serena documentation

Read the following documentation to understand Serena's capabilities and setup process:

- Load <https://raw.githubusercontent.com/oraios/serena/refs/heads/main/README.md> to understand what Serena is and its capabilities
- Load <https://oraios.github.io/serena/02-usage/020_running.html> to learn how to run Serena
- Load <https://oraios.github.io/serena/02-usage/030_clients.html> to learn how to configure your MCP client
- Load <https://oraios.github.io/serena/02-usage/040_workflow.html> to learn how to setup Serena for your project

## 4. Guide user through setup process

Based on the loaded documentation:

1. **Check prerequisites**: Verify that `uv` is installed (required for running Serena)
2. **Identify client type**: Determine which MCP client the user is using (Claude Code, Claude Desktop, Cursor, VSCode, etc.)
3. **Provide setup instructions**: Guide through the configuration specific to their client if it not already configured
4. **Setup project**: Guide through the project setup process if it not already setup
5. **Start indexing project**: Guide through the project indexing process if it was just setup
6. If MCP was just setup, ask user to restart Claude Code to load the new MCP server, write to user explisit instructions, including "exit claude code console, then run 'claude --continue' and then write "continue" to continue setup process"
7. **Test connection**: Verify that Serena tools are accessible after setup
   1. If not yet, run initial_instructions
   2. Check if onboarding was performered, if not then run it.
   3. Then try to read any file

After adding MCP server, but before testings connection write to user this message EXACTLY:

```markdown
You must restart Claude Code to load the new MCP server:

  1. Exit Claude Code console (type exit or press Ctrl+C)
  2. Run claude --continue
  3. Type "continue" to resume setup

  After restart, I will:
  - Verify Serena tools are accessible
  - Run initial_instructions if needed
  - Perform onboarding for this project (if not already done)

```

## 5. Update CLAUDE.md file

Use the path determined in step 1. Once Serena is successfully set up, update the appropriate CLAUDE.md file with the following content EXACTLY:

```markdown
### Use Serena MCP for Semantic Code Analysis instead of regular code search and editing

Serena MCP is available for advanced code retrieval and editing capabilities.

**When to use Serena:**
- Symbol-based code navigation (find definitions, references, implementations)
- Precise code manipulation in structured codebases
- Prefer symbol-based operations over file-based grep/sed when available

**Key tools:**
- `find_symbol` - Find symbol by name across the codebase
- `find_referencing_symbols` - Find all symbols that reference a given symbol
- `get_symbols_overview` - Get overview of top-level symbols in a file
- `read_file` - Read file content within the project directory

**Usage notes:**
- Memory files can be manually reviewed/edited in `.serena/memories/`

```

Add this section, if server setup at user level (global):

```markdown

**Project setup (per project):**
1. Run `serena project create --index` in your project directory
2. Serena auto-detects language; creates `.serena/project.yml`
3. First use triggers onboarding and creates memory files in `.serena/memories/`
```

## 6. Project initialization (if needed)

If this is a new project or Serena hasn't been initialized:

1. Guide user to run project initialization commands
2. Explain project-based workflow and indexing
3. Configure project-specific settings if needed
