---
name: setup-context7-mcp
description: Guide for setup Context7 MCP server to load documentation for specific technologies.
argument-hint: List of languages and frameworks to load documentation for
---

User Input:

```text
$ARGUMENTS
```

# Guide for setup Context7 MCP server

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

## 2. Check if Context7 MCP server is already setup

Check whether you have access to Context7 MCP server by making request.

if no, load <https://raw.githubusercontent.com/upstash/context7/refs/heads/master/README.md> file and guide user through setup process that applicable to agent/operation system.

## 3. Update CLAUDE.md file

Use the path determined in step 1:

- Parse user input, if it empty read current project structure and used technologies, if project empty ask user to provide list of languages and frameworks that planned to be used in this project.
- Search through context7 MCP for relevant technologies documentation
- Update the appropriate CLAUDE.md file with following content:

```markdown
### Use Context7 MCP for Loading Documentation

Context7 MCP is available to fetch up-to-date documentation with code examples.

**Recommended library IDs**:

- `[doc-id]` - short description of documentation

```
