---
title: Add support for Gemini and Antigravity CLI
---

## Initial User Prompt

add support for gemini and antigravity cli

### Context

Currently used in README.md approach with isntallation through `vercel-labs/skills` not works well with majority of providers due to lack of support for agents installation from vercel-labs/skills cli.

But gemini have own standard for extensions, that uses gemini-extension.json and antigravity cli uses plugin.json

#### Gemini CLI: use an extension

Gemini CLI extensions can bundle both Agent Skills and subagents:

```
my-gemini-extension/
├── gemini-extension.json
├── skills/
│   └── code-review/
│       ├── SKILL.md
│       └── scripts/
└── agents/
    ├── reviewer.md
    └── researcher.md
```
Minimal manifest:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "My skills and specialized agents"
}
```
Install it with:

```bash
gemini extensions install https://github.com/your-org/my-gemini-extension
```

#### Antigravity CLI: use a native plugin

Antigravity CLI has a plugin system specifically designed to package skills, agents, rules, MCP servers, and hooks:

```
my-antigravity-plugin/
├── plugin.json
├── skills/
│   └── code-review/
│       └── SKILL.md
├── agents/
│   ├── reviewer.md
│   └── researcher.md
├── mcp_config.json
├── hooks.json
└── rules/
```
Manifest:

```json
{
  "$schema": "https://antigravity.google/schemas/v1/plugin.json",
  "name": "my-plugin",
  "description": "My skills and specialized subagents"
}
```

### Requirements

Key constraint driving this design: neither Gemini CLI nor Antigravity CLI has a marketplace/registry concept (unlike Claude Code's `marketplace.json`) — each install command installs exactly one extension/plugin, and a remote/URL-based `gemini extensions install` clones the whole repo and requires the manifest at the **repo root**, with no subdirectory support. So per-plugin selective install (like `/plugin install reflexion@...`) isn't achievable for Gemini/Antigravity; instead, all plugins' `skills/`/`agents/` content is merged into one root-level bundle installable as a single extension/plugin.

#### 1. Repo structure & build output (generated, committed by CI)

- At the repo root: `gemini-extension.json` (`name`/`version`/`description` sourced from `.claude-plugin/marketplace.json`'s top-level fields) and `plugin.json` (Antigravity schema, same source fields; only used by the antigravity-only fallback install, not the primary flow).
- At the repo root: `skills/` and `agents/` — union of every `plugins/<name>/skills/*` and `plugins/<name>/agents/*` folder, copied as-is with original names preserved (no prefixing, no nesting).
- Collision policy: if two plugins define a same-named skill/agent folder, the sync must hard-fail with an error naming both source plugins. Names are currently unique across all plugins.
- Per-plugin outcome: every plugin merges whatever `skills/`/`agents/` it has (including `reflexion`'s `skills/`). `reflexion`'s `hooks/` folder is left out of the merge — not a skip of the plugin, hooks were never a sync target. `ddd` and `tech-stack` are `rules/`-only today so they contribute nothing to the merge (not a special-case exclusion — if they ever add `skills/`/`agents/`, it merges automatically). Other plugins' non-skills/agents folders (`scripts/`, `tasks/`, `prompts/` in `mcp`/`sadd`/`sdd`/`fpf`) stay untouched in place.

#### 2. justfile: `sync-provider-formats`

- Plain bash in the justfile (matching `sync-docs-to-plugins`/`sync-plugins-to-docs` style), using `jq` for manifest generation — no external script files.
- Full regeneration every run: delete and rebuild `skills/`, `agents/`, `gemini-extension.json`, `plugin.json` from scratch (no incremental patching), so removed plugin content disappears from the bundle automatically.
- Idempotent: re-running with no plugin changes produces an identical output (no git diff).

#### 3. GitHub Action (CI)

- Triggers on `pull_request`, scoped with a path filter to `plugins/**/skills/**`, `plugins/**/agents/**`, and `.claude-plugin/marketplace.json` (avoids running on unrelated PRs, e.g. docs-only changes).
- Runs `just sync-provider-formats`, then diffs the result against what's committed.
- If different and the PR branch is same-repo (not a fork): commit and push the regenerated files back onto the PR branch.
- If different and the PR is from a fork: fail the check with an instructive message (run `just sync-provider-formats` locally and commit) — GitHub Actions' default token can't push to fork branches.
- If the sync script itself errors (name collision): fail the check without committing anything, surfacing the conflict directly.

#### 4. README installation instructions

Convert `### Step 1: Install Marketplace and Plugins` to four sibling `<details><summary>` spoilers (not subheadings):

1. **Claude Code** — unchanged (`/plugin marketplace add`, `/plugin install <name>@...`).
2. **Gemini CLI or Antigravity CLI** (new) — primary flow:
   ```bash
   gemini extensions install https://github.com/NeoLabHQ/context-engineering-kit
   agy plugin import gemini
   ```
   Antigravity-only fallback (no Gemini CLI installed):
   ```bash
   git clone https://github.com/NeoLabHQ/context-engineering-kit
   cd context-engineering-kit
   agy plugin install .
   ```
   Note inline: installs every plugin's skills/agents as one bundle — no per-plugin selection like Claude Code's `/plugin install`; content from `rules/`-only plugins (`ddd`, `tech-stack`) and `reflexion`'s `hooks/` isn't included.
3. **Cursor, Codex, OpenCode and others** — existing `npx skills add` flow (Antigravity removed from this heading, since it now has its own native spoiler above). Add caveat: each provider uses its own agent format, so this path won't give subagent-using plugins the full experience — only skills transfer cleanly.
4. **Alternative installation methods** (OpenSkills) — existing content, promoted from a nested spoiler to a top-level sibling spoiler.




## Description

// Will be filled in future stages by business analyst
