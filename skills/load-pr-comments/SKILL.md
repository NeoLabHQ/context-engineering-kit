---
name: load-pr-comments
description: Use to load open/unresolved PR review comments then aggregate them as tasks in .specs/comments/*.md for parallel agents to fix.
argument-hint: Optional PR number or URL - defaults to the PR of the current git branch
---

# Load Unresolved PR Review Comments as Parallel Tasks

Load ONLY open/UNRESOLVED PR review threads and rewrite them into grouped markdown task files under `.specs/comments/*.md`, each safe for a separate parallel agent to implement with no overlap.

## Critical Guidelines

- You MUST load ONLY threads where the resolved state is false. Skip resolved threads.
- You MUST rewrite each comment as an actionable TASK requirement, not a summary. Preserve substance (code suggestions, exact instructions) verbatim.
- You MUST NOT post, reply to, or modify anything on GitHub. This skill is read-only against the API.
- You MUST group comments so each file is independently implementable with NO duplication across files.

## Step 0: Verify what tools are available

1. Check if GitHub CLI is installed and authenticated:

   ```bash
   gh auth status
   ```

2. Check if the GitHub MCP server is available:

   ```bash
   mcp__MCP_DOCKER__pull_request_read
   ```
   or simular command without `MCP_DOCKER` prefix, if installed directly.

- if both are available, use any that have enough accesses to the repository.
- if github mcp server avaiable but have different structure, adjust in order to fit the expected structure.
- if none is available, try to load directly through curl in case if it is public repository. If it is private, ask user to install GitHub CLI or GitHub MCP server.
- if MCP server not installed, but github cli is installed, but not authenticated, ask user to run `gh auth login` to authenticate.

## Step 1: Resolve the Target PR

- An explicit PR argument ALWAYS takes precedence over current-branch resolution. If a PR number or URL was passed, use it (a URL like `https://github.com/{owner}/{repo}/pull/{n}` → number `{n}`) and do NOT consult the current branch.
- Otherwise default to the PR of the CURRENT branch:

```bash
gh pr view --json number,url,headRefName   # current branch's PR
```

- Resolve repo owner/name: `gh repo view --json owner,name`.
- If no PR exists for the branch, `gh pr view` errors with "no pull requests found" — STOP and report that no PR is associated with the branch (ask for a PR number/URL).

## Step 2: Retrieve UNRESOLVED Comments

Resolved/unresolved is a GraphQL `reviewThreads { isResolved }` concept — the REST `/pulls/{n}/comments` endpoint does NOT expose it. Use one of the two approaches below; if the primary is unavailable, fall back to the other.

### Primary: gh CLI (GraphQL)

Filter `isResolved == false` directly in the jq:

```bash
gh api graphql -f query='
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      reviewThreads(first:100){
        nodes {
          isResolved
          isOutdated
          path
          line
          startLine
          originalLine
          comments(first:50){
            nodes { author{login} body diffHunk url }
          }
        }
      }
    }
  }
}' -F owner=OWNER -F repo=REPO -F pr=PR_NUMBER \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[]
         | select(.isResolved==false)
         | {path, isOutdated,
            line: (.line // .startLine // .originalLine),
            comments: [.comments.nodes[]
             | {author: .author.login, url, body, diffHunk}]}]'
```

This returns each unresolved thread with its file `path`, an `isOutdated` flag, a usable `line`, and ordered comments (author, body, permalink `url`, `diffHunk`).

IMPORTANT: For OUTDATED threads `line` is `null` (the diff moved). The jq above already falls back `line // startLine // originalLine`, so `line` is never null when any anchor exists. When ALL three are null, omit the `:<line>` segment entirely in the template — never render `path:null`.

### Fallback: GitHub MCP

If the GitHub MCP server (`MCP_DOCKER`) is available, use the `mcp__MCP_DOCKER__pull_request_read` tool with `method: "get_review_comments"`:

```
mcp__MCP_DOCKER__pull_request_read
  method: "get_review_comments"
  owner: "OWNER"
  repo: "REPO"
  pullNumber: PR_NUMBER
  perPage: 100
```

It returns `review_threads[]`, each with `is_resolved`, `is_outdated`, `is_collapsed` (all snake_case — verified against this tool's response) and `comments[]` (`body`, `path`, `author`, `html_url`). Keep only threads where `is_resolved` is `false`. Note the MCP comment objects expose `path` but NOT a line number, so use the `html_url` as the location anchor. Paginate with `after: <endCursor>` while `pageInfo.hasNextPage` is true.

## Step 3: Group and Rewrite as Tasks

Convert unresolved threads into focused task files for parallel agents.

Deduplicate FIRST (before grouping): if two or more threads request the same change at the same `path` (and same/overlapping line), or carry an identical suggested fix, collapse them into ONE requirement. Do not emit a separate line item per duplicate thread — this matters most in the nitpick file where repeated trivial suggestions cluster.

Rewrite rules per thread:

- Drop conversation framing and author names. Output a task, not a transcript.
- If a HUMAN reviewer left feedback, write THAT as the requirement.
- If only a bot/AI suggestion exists (Claude, CodeRabbit, Copilot, etc.), write that fix suggestion as the requirement.
- Preserve substance — do NOT summarize away code blocks, suggested diffs, or exact wording.
- Add context: a short issue description and a link to the file/line (the comment `url`/`html_url`, plus `path:line`) when available. If `line` is null (outdated/unanchorable thread), write just `path` with no `:line` segment and note it is outdated.

Before/after (lock in "rewrite as task, do not summarize"):

- Raw thread (bot): "commands is incorrect, real commands is more like ```/add-task /plan-task /implement-task```"
- Task requirement: "- [ ] Replace the listed commands with the correct ones: `/add-task`, `/plan-task`, `/implement-task`" (suggestion preserved verbatim, conversation framing dropped — NOT "fix the commands").

Grouping rules:

- Group by file or by functionality so two agents never touch the same area → NO conflicts, NO duplicated work.
- Do NOT duplicate a comment across files.
- Aggregate nitpicks / trivial one-line changes into ONE combined file (e.g. `nitpicks.md`).
- Cap at ≤5 files total. Do NOT over-combine unrelated changes — each file must be a single, focused, independently-implementable unit of work.

## Step 4: .gitignore Handling

Ensure generated comment files are ignored. This is idempotent: it appends the entry only if missing, and `>>` CREATES `.gitignore` if it does not exist.

```bash
grep -qF '.specs/comments/*.md' .gitignore 2>/dev/null || printf '\n.specs/comments/*.md\n' >> .gitignore
```

## Step 5: Write Files

```bash
mkdir -p .specs/comments
```

Write each group as `.specs/comments/<kebab-topic>.md` using this template:

```markdown
# Tasks: <focused topic, e.g. Fix incorrect command names in README-zh>

## <Topic 1>

File: `<path>:<line>` (omit `:<line>` when line is null; append " (outdated)" if isOutdated)
<Issue description for the change>

### Requirements

- [ ] <Reviewer requirement or bot fix suggestion, substance preserved>
- [ ] <Next requirement in this topic>

## <Topic 2>

File: `<path>:<line>` 
<Issue description for the change>

### Requirements

- [ ] <Reviewer requirement or bot fix suggestion, substance preserved>
- [ ] <Next requirement in this topic>

```

## Step 6: Report

Summarize: target PR (number + url), count of unresolved threads loaded, files created with their topics, and any threads skipped (resolved) or limitations hit (e.g. MCP unavailable).

## Edge Cases

| Situation | Handling |
|-----------|----------|
| No PR for current branch | `gh pr view` errors → report and request a PR number/URL |
| Argument is a URL | Extract trailing number after `/pull/` |
| Zero unresolved threads | Create no files; report "no unresolved comments" |
| >100 threads | Paginate (GraphQL `after` cursor / MCP `after`) |
| MCP unavailable | Use gh GraphQL; if both unavailable, report limitation |
| Only resolved threads exist | Skip all; report none actionable |
