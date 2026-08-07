---
name: resolve-fixed-pr-comments
description: Verify what PR review comments have been addressed (committed/pushed OR uncommitted local changes) and resolve the threads that are genuinely fixed or no longer relevant.
---

# Resolve Fixed PR Review Comments

Load ONLY open/UNRESOLVED PR review threads, verify each one against the CURRENT state of the codebase (the fix may be committed/pushed OR exist only as uncommitted local changes — both count), and resolve ONLY the threads that are genuinely fixed or no longer relevant. The single permitted write action is resolving a thread. Nothing else is touched.

## Critical Guidelines

**Violating the letter of these rules means failing the task.** If you fail the task, you will be killed!

- When unsure, LEAVE THE THREAD UNRESOLVED. Better to leave a fixed comment unresolved than to wrongly resolve an unfixed one.
- You MUST load ONLY threads where `isResolved`/`is_resolved` is false. Skip resolved threads.
- You MUST observe only the CURRENT state of the codebase. Read the file as it exists NOW. Do NOT reason about how the code used to be, what a commit changed, or git history as evidence of a fix — only whether the requirement is satisfied in the current files counts.
- A fix is VALID whether it is already committed/pushed OR exists only as uncommitted local changes. Both are acceptable evidence. Inspect the working tree as-is.
- You MUST NOT modify code, create/edit/delete any file, or run tests, linters, formatters, or builds.
- You MUST NOT push, pull, commit, stash, checkout, switch, reset, revert, rebase, merge, cherry-pick, or perform ANY mutating git operation. ONLY read-only inspection (`git status`, `git diff`, `git log`, `git branch`) is allowed, and only to observe the current state.
- You MUST NOT add a comment to the PR, reply to a thread, submit a review, approve, or request changes. The ONLY write action permitted against GitHub is resolving a thread that is genuinely fixed.
- You MUST be critical and perfectionist. A comment is "fixed" ONLY when ALL of its requirements are FULLY satisfied in the current codebase. Partially-addressed comments, unaddressed nitpicks, and "close enough" changes stay UNRESOLVED.
- You MUST NOT resolve a thread you did not verify against an actual file. No verification → no resolve.

## Red Flags - STOP and Leave Unresolved

If any of these describe your reasoning, do NOT resolve the thread:

- "The fix is probably there, I'll resolve it." → No. Verify against the current file or leave it.
- "The commit message says it was fixed." → Commit messages and history are NOT evidence. Read the current file.
- "Most of the comment is addressed." → Partial ≠ fixed. Leave unresolved.
- "It's just a nitpick, resolving it cleans up the PR." → Unaddressed nitpicks stay unresolved.
- "It's no longer relevant because the code moved." → Only resolve if the requirement is genuinely satisfied or genuinely obsolete in the CURRENT code — not because it's inconvenient to verify.
- "I'll quickly fix it myself, then resolve." → FORBIDDEN. No code edits. If it isn't already fixed, leave it unresolved.
- "I'll reply explaining why I resolved it." → FORBIDDEN. No replies, no comments. Resolve silently or leave it.
- "I'll resolve all of them since the branch looks done." → Resolve per-thread, each on its own verified evidence.

### Rationalization Table

| Excuse | Reality |
|--------|---------|
| "The fix was committed, so it's done." | Read the CURRENT file and confirm the requirement is satisfied. Committed ≠ verified. |
| "Git diff shows the change." | A diff is historical reasoning. Confirm the requirement holds in the current file content, not that something changed. |
| "It's uncommitted, so it doesn't count yet." | Uncommitted local changes ARE valid evidence. Inspect the working tree as-is. |
| "I'll just make the small fix and resolve." | Editing code is strictly forbidden. Unfixed → unresolved. |
| "A reply would be polite." | No replies/comments. The only write action is resolving. |
| "Nitpick is trivial, resolve to tidy up." | Unaddressed = unresolved, regardless of triviality. |
| "Reviewer would obviously accept this." | You are not the reviewer. Resolve only on satisfied requirements, not on predicted approval. |
| "Not 100% sure, but likely fixed." | Unsure = leave unresolved. |

## How to Use

Work one thread at a time: (1) load unresolved threads with their GraphQL node `id`, (2) for each, read the current file(s) referenced and check every requirement against the present content, (3) resolve ONLY if fully satisfied/obsolete, otherwise skip. Report what was resolved and what was left and why.

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
          id
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
         | {id, path, isOutdated,
            line: (.line // .startLine // .originalLine),
            comments: [.comments.nodes[]
             | {author: .author.login, url, body, diffHunk}]}]'
```

This returns each unresolved thread with its GraphQL node `id` (needed to resolve it in Step 4), its file `path`, an `isOutdated` flag, a usable `line`, and ordered comments (author, body, permalink `url`, `diffHunk`).

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

> The MCP review-thread object also carries the thread node `id` (the `PRRT_...` node ID). Capture it per thread — `mcp__MCP_DOCKER__pull_request_review_write` with `method: "resolve_thread"` needs it in Step 4.

## Step 3: Verify Each Thread Against the CURRENT Codebase

For EACH unresolved thread, gather the concrete requirement(s) and verify them against the present file content. Apply the Critical Guidelines strictly.

1. Identify what the comment actually requires. If a HUMAN reviewer left feedback, the requirement is THAT feedback. If only a bot/AI suggestion exists (Claude, CodeRabbit, Copilot, etc.), the requirement is that suggested fix. A thread may contain multiple requirements — ALL must be satisfied to count as fixed.
2. Open the referenced file(s) at `path` and read the CURRENT content (use the Read tool / `git show :<path>` is NOT needed — just read the working-tree file). Optionally run `git diff -- <path>` or `git status` ONLY to observe current uncommitted changes; never to reason about history as proof.
3. Decide the disposition:

| Disposition | Condition | Action |
|-------------|-----------|--------|
| FIXED | Every requirement in the thread is fully satisfied in the current file content (committed OR uncommitted). | Mark to resolve in Step 4. |
| OBSOLETE | The code the comment referred to genuinely no longer exists / the concern is genuinely moot in the current code. | Mark to resolve in Step 4. |
| NOT FIXED | Any requirement is unmet, partially met, or you cannot confirm it from the current files. | LEAVE UNRESOLVED. Do nothing. |
| UNSURE | You cannot confidently verify satisfaction. | LEAVE UNRESOLVED. Do nothing. |

Do NOT edit code to make a thread pass. Do NOT run tests/builds/linters to "check". Verification is reading the current source and judging whether the requirement is met.

## Step 4: Resolve the Genuinely-Fixed Threads

For each thread marked FIXED or OBSOLETE, resolve it using the thread's node `id` captured in Step 2. Use whichever path is available (prefer the one you used to load comments). Resolving an already-resolved thread is a harmless no-op.

### Primary: gh CLI (GraphQL `resolveReviewThread` mutation)

The `resolveReviewThread` mutation takes a `ResolveReviewThreadInput` whose required field is `threadId` (the GraphQL node `id` from Step 2's `reviewThreads.nodes[].id`). Verified against GitHub's GraphQL schema via introspection (`ResolveReviewThreadInput.threadId: ID!`).

```bash
gh api graphql -f query='
mutation($threadId:ID!){
  resolveReviewThread(input:{threadId:$threadId}){
    thread { id isResolved }
  }
}' -F threadId='PRRT_kwDOxxxxxxxxxxxxxxxx'
```

On success the response is `{"data":{"resolveReviewThread":{"thread":{"id":"PRRT_...","isResolved":true}}}}`. Confirm `isResolved` is `true`.

### Fallback: GitHub MCP (`pull_request_review_write` → `resolve_thread`)

The GitHub MCP server CAN resolve threads via `mcp__MCP_DOCKER__pull_request_review_write` with `method: "resolve_thread"`. It requires only `threadId` (the thread node ID, e.g. `PRRT_kwDOxxx`). Per the tool's own documentation, `owner`/`repo`/`pullNumber` are NOT used by this method, but the tool schema marks them required — pass the PR's owner/repo/pullNumber to satisfy validation; they are ignored for the resolve operation.

```
mcp__MCP_DOCKER__pull_request_review_write
  method: "resolve_thread"
  threadId: "PRRT_kwDOxxxxxxxxxxxxxxxx"
  owner: "OWNER"
  repo: "REPO"
  pullNumber: PR_NUMBER
```

If the MCP server is NOT available or its `pull_request_review_write` lacks `resolve_thread`, fall back to the gh CLI GraphQL mutation above.

> ONLY `resolve_thread` is permitted. Do NOT use `unresolve_thread`, `create`, `submit_pending`, `delete_pending`, or any `event` (APPROVE/REQUEST_CHANGES/COMMENT) — those are write actions this skill forbids.

### Parameters Explained

| Parameter | Path | Type | Required | Description |
|-----------|------|------|----------|-------------|
| `threadId` | gh CLI & MCP | string (`ID!`) | Yes | The review thread's GraphQL node id (`reviewThreads.nodes[].id`, e.g. `PRRT_kwDO...`). This is the thread id, NOT a comment id and NOT a numeric REST id. |
| `method` | MCP | string | Yes (MCP) | Must be `"resolve_thread"`. |
| `owner` | MCP | string | Yes (MCP schema) | Repo owner. Ignored by `resolve_thread` but required by the tool schema. |
| `repo` | MCP | string | Yes (MCP schema) | Repo name. Ignored by `resolve_thread` but required by the tool schema. |
| `pullNumber` | MCP | number | Yes (MCP schema) | PR number. Ignored by `resolve_thread` but required by the tool schema. |
| `clientMutationId` | gh CLI | string | No | Optional dedupe token on the GraphQL input. Omit normally. |

## Step 5: Report

Summarize without taking any further action:

- Target PR (number + url).
- Count of unresolved threads loaded.
- Threads RESOLVED, each with its `path:line` (or `path` if outdated) and a one-line reason (FIXED / OBSOLETE) plus the evidence in the current code.
- Threads LEFT UNRESOLVED, each with a one-line reason (NOT FIXED / partial / UNSURE).
- Any limitation hit (e.g. MCP unavailable, all threads already resolved).

## Examples

**Input:** `resolve-fixed-pr-comments` (no argument, current branch has PR #42)

**Process:** Load PR #42's unresolved threads (Step 2). Thread A on `src/auth.ts:30` requires "add error handling for invalid token". Read current `src/auth.ts` — a `try/catch` now wraps the token check (uncommitted local change). Disposition FIXED → resolve via `resolveReviewThread(threadId: "PRRT_...")`. Thread B on `README.md:10` is a nitpick "fix typo 'teh'". Read current `README.md` — still says "teh". Disposition NOT FIXED → leave unresolved.

**Output:** "PR #42: 2 unresolved threads loaded. Resolved 1 — src/auth.ts:30 (FIXED: try/catch added around token validation in working tree). Left unresolved 1 — README.md:10 (NOT FIXED: 'teh' typo still present)."

**Input:** `resolve-fixed-pr-comments https://github.com/acme/app/pull/7`

**Process:** Argument takes precedence over current branch. PR #7. One thread requires renaming `getUser` → `fetchUser` AND updating its callers. Current code renamed the function but one caller still uses `getUser`. Requirement only partially met → NOT FIXED → leave unresolved.

**Output:** "PR #7: 1 unresolved thread loaded. Resolved 0. Left unresolved 1 — src/user.ts:12 (NOT FIXED: function renamed but caller in src/page.ts:5 still calls getUser)."

## Troubleshooting / Common Issues

| Situation | Handling |
|-----------|----------|
| No PR for current branch | `gh pr view` errors → report and request a PR number/URL. |
| Argument is a URL | Extract trailing number after `/pull/`. |
| Zero unresolved threads | Resolve nothing; report "no unresolved comments". |
| >100 threads | Paginate (GraphQL `after` cursor / MCP `after`) before verifying. |
| MCP unavailable | Use gh GraphQL for both loading and resolving; if both unavailable, report limitation. |
| MCP `resolve_thread` rejects missing owner/repo/pullNumber | The tool schema requires them even though the method ignores them — pass the PR's owner/repo/pullNumber. |
| `Could not resolve to a node with the global id` | Wrong id — ensure you pass the thread node `id` (`PRRT_...`) from `reviewThreads.nodes[].id`, not a comment id or numeric REST id. |
| Resolve mutation returns `isResolved: true` for a thread you didn't mean to touch | You resolved the wrong thread — there is no safe auto-undo permitted by this skill (unresolve is a forbidden write); report it to the user. |
| Fix exists only as uncommitted changes | Valid evidence — inspect the working-tree file and resolve if the requirement is satisfied. |
| Cannot confirm a requirement from current files | Leave the thread UNRESOLVED. Never resolve on assumption. |
| Tempted to edit code so a thread passes | Forbidden. No code modifications. Unfixed stays unresolved. |
