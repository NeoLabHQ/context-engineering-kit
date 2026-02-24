# Context Engineering Kit

Claude Code plugin marketplace with advanced context engineering techniques focused on improving agent result quality.

## Project Structure

```
context-engineering-kit/
├── .claude-plugin/
│   └── marketplace.json    # Main marketplace manifest with all plugins
├── plugins/                 # Plugin source code
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json  # Plugin manifest
│       ├── README.md
│       ├── commands/        # Slash commands (*.md)
│       └── skills/          # Skills (*.md)
├── docs/                    # Documentation (GitBook)
│   └── plugins/
│       └── <plugin-name>/   # Plugin documentation
│           └── README.md
├── specs/                   # Feature specifications
├── justfile                 # Development commands
└── CONTRIBUTING.md          # Contribution guidelines
```

## Available Plugins

code-review, customaize-agent, ddd, docs, git, kaizen, mcp, reflexion, sadd, sdd, tdd, tech-stack

## Development Commands

```bash
just help                                       # Show all commands
just list-plugins                               # List plugins with versions
just sync-docs-to-plugins                       # Copy docs/plugins/*/README.md → plugins/*/README.md
just sync-plugins-to-docs                       # Copy plugins/*/README.md → docs/plugins/*/README.md
just set-version <name> <x.y.z>                 # Update plugin version
just set-marketplace-version <x.y.z>            # Update marketplace version
```

## Key Development Rules

### Plugin Design Philosophy

1. **Commands over skills** - Commands load on-demand; skill descriptions load into context by default
2. **Specialized agents** - Use agents with focused context to reduce hallucinations
3. **Setup-commands** - Use setup commands to update CLAUDE.md for persistent project context
4. **Minimal tokens** - Every token counts; keep prompts concise

### When Creating/Modifying Plugins

- Use `just set-version <name> <x.y.z>` to update plugin versions consistently, do not modify manually.
- Use `just set-marketplace-version <x.y.z>` to update the marketplace version, do not modify manually.
- Keep README.md in sync between `plugins/<name>/` and `docs/plugins/<name>/` using `just sync-docs-to-plugins` and `just sync-plugins-to-docs` commands. Do not update both manually.
- Test plugins with Claude Code before committing using `plugins/customaize-agent:test-prompt` and `plugins/customaize-agent:test-skill` commands.

### When Adding New Skills or Commands

**Documentation Checklist** (all files must be updated):

1. `plugins/<name>/README.md` - Add skill/command with "Use when..." trigger and structured tables
2. `README.md` (root) - Add to Skills/Commands section under plugin listing
3. `docs/reference/skills.md` or `docs/reference/commands.md` - Add to complete reference
4. `docs/plugins/README.md` - Update Key Features for the plugin
5. `docs/resources/related-projects.md` - Add source project attribution if based on external work
6. `docs/resources/papers.md` - Add research papers if technique is based on academic research
7. Run `just sync-plugins-to-docs` to sync plugin README to docs/
8. Bump plugin version: `just set-version <name> <x.y.z>` (minor for features)
9. Bump marketplace version: `just set-marketplace-version <x.y.z>`

**Finding All References**: Before declaring documentation complete, search for all files referencing the plugin:

```bash
grep -r "<plugin-name>" docs/ README.md --include="*.md" -l
```

**Skill Documentation Pattern**:

- Start with "Use when..." trigger phrase
- Use tables for structured information (not prose)
- Include key concepts with one-line explanations
- Keep YAML `name:` field matching folder name for consistency

### When Creating/Refactoring Agents

**Agent File Location**: `.claude/agents/<agent-name>.md` or `plugins/<plugin>/agents/<agent-name>.md`

See `plugins/customaize-agent/commands/create-agent.md` command for detailed agent creation guidelines including frontmatter rules, required sections, process ordering, and decision table patterns.

## Use Context7 MCP for Loading Documentation

Context7 MCP is available to fetch up-to-date documentation with code examples.

**Recommended library IDs**:

- `/anthropics/claude-code` - Claude Code CLI tool documentation (1954 snippets)
- `/websites/platform_claude` - Claude Developer Platform comprehensive docs (5916 snippets)
- `/anthropics/anthropic-cookbook` - Code examples and guides for building with Claude (1226 snippets)
- `/anthropics/courses` - Anthropic educational courses on SDK and prompt engineering (1173 snippets)
- `/websites/platform_claude_en_agent-sdk` - Claude Agent SDK for Python/TypeScript (605 snippets)
- `/anthropics/claude-agent-sdk-python` - Python SDK for Claude Agent (57 snippets)
- `/anthropics/claude-code-sdk-python` - Python SDK for Claude Code (31 snippets)

**Usage**:

```
mcp__context7__query-docs libraryId: "/anthropics/claude-code" query: "how to configure hooks"
```

## Use Paper Search MCP for Academic Research

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

## Use Minibeads for Task Tracking

Minibeads is a task tracking tool that allow to create tasks as markdown files.

You MUST: Use `"md create"` for issues, TodoWrite for simple single-session execution

### Essential Commands

#### Finding Work

- `mb ready` - Show issues ready to work (no blockers)
- `mb list --status=open` - All open issues
- `mb list --status=in_progress` - Your active work
- `mb show <id>` - Detailed issue view with dependencies

#### Creating & Updating

- `mb create "title" -t task|bug|feature -p 2 -d "description"` - New issue
  - Priority: 0-4 or P0-P4 (0=critical, 2=medium, 4=backlog). NOT "high"/"medium"/"low"
- `mb update <id> --status=in_progress` - Claim work
- `mb update <id> --assignee=username` - Assign to someone
- `mb close <id>` - Mark complete
- `mb close <id1> <id2> ...` - Close multiple issues at once (more efficient)
- `mb close <id> --reason=\"explanation\"` - Close with reason
- **Tip**: When creating multiple issues/tasks/epics, use parallel subagents for efficiency

#### Modifying Task Descriptions

**Use Write tool instead of `mb update -d` for description changes:**

Tasks are stored as markdown files in `.beads/issues/<id>.md` with this format:

```yaml
---
[task frontmatter]
---

# Description

[Task description content here]
```

**Why Write tool for descriptions?**

- `mb update -d` replaces entire description (easy to lose content)
- Write tool allows precise edits while preserving existing content
- Better for large descriptions with multiple sections

#### Dependencies & Blocking

- `mb dep add <issue> <depends-on>` - Add dependency (issue depends on depends-on)
- `mb blocked` - Show all blocked issues
- `mb show <id>` - See what's blocking/blocked by this issue

### Common Workflows

**Starting work:**

```bash
mb ready           # Find available work
mb show <id>       # Review issue details
mb update <id> --status=in_progress  # Claim it
mb close <id1> <id2> ...    # Close all completed issues at once
```

**Creating dependent work:**

```bash
# Run mb create commands in parallel (use subagents for many items)
mb create "Implement feature X" -t feature
mb create "Write tests for X" -t task
mb dep add cek-yyy cek-xxx  # Tests depend on Feature (Feature blocks tests)
```

### Examples

**CREATING ISSUES**

- mb create "Fix login bug"
- mb create "Add auth" -p 0 -t feature
- mb create "Write tests" -d "Unit tests for auth" --assignee alice

**VIEWING ISSUES**

- mb list       List all issues
- mb list --status open  List by status
- mb list --priority 0  List by priority (0-4, 0=highest)
- mb show cek-1       Show issue details

## Problems and Solutions

Memory of found issues and stategies to solve them.

### When Claude sees code blocks with Thought:, Action:, Observation: patterns, it interprets them as output templates to mimic, not as instructions to execute

So instead of actually calling Write() tool, it generates text that says:
Thought: Let me analyze...
Action: Write(.specs/scratchpad/...)

This is just text output - not a real tool invocation.

Why This Happens

1. Code blocks look like output format - Claude thinks "this is what my response should look like"
2. Pattern mimicking - The agent copies the pattern structure as text instead of executing tools
3. Pseudo-code confusion - Action: Write(...) looks like code to output, not a command to run

#### The Fix

Remove all Thought-Action-Observation code block examples and replace with imperative natural language instructions that tell the agent WHAT to do, trusting it knows HOW to use tools.

Instead of:
Thought: I need to read the task file...
Action: Read(.specs/tasks/task-example.md)
Observation: [What I found...]

Write:
First, use the Read tool to load the task file. Then analyze what the user is requesting and document your findings in the scratchpad using the Write tool.
