# /git:resolve-fixed-pr-comments - Resolve Fixed PR Review Comments

Load open/unresolved PR review threads, verify each one against the CURRENT state of the codebase, and resolve ONLY the threads that are genuinely fixed or no longer relevant. The single permitted write action is resolving a thread.

Use when PR review comments have been addressed (committed/pushed OR uncommitted local changes) and the resolved review threads need to be closed.

**Key Concepts**

| Concept | Description |
|---------|-------------|
| Load scope | Only `isResolved == false` threads, each with its GraphQL node `id` |
| Evidence | Current file content — committed/pushed OR uncommitted local changes both count |
| No history reasoning | Verifies the requirement in current files, not what a commit changed |
| Disposition | FIXED / OBSOLETE → resolve; NOT FIXED / UNSURE → leave unresolved |
| Resolve action | `resolveReviewThread` GraphQL mutation (gh CLI) or MCP `resolve_thread` |

**Hard Constraints (read-only discipline)**

| Forbidden | Detail |
|-----------|--------|
| Modify code | No create/edit/delete of any file |
| Run tooling | No tests, linters, formatters, or builds |
| Mutate git | No push/pull/commit/stash/checkout/reset/revert/rebase/merge/cherry-pick |
| Reply/comment | No PR comments, thread replies, review submissions, approvals |
| Resolve unfixed | A thread is fixed ONLY when ALL its requirements are fully satisfied now |

Allowed git is read-only inspection only: `git status`, `git diff`, `git log`, `git branch`.

**Quick Reference**

| Task | Approach |
|------|----------|
| Verify tooling | `gh auth status`; check GitHub MCP availability |
| Resolve target PR | Argument (number/URL) takes precedence over `gh pr view` current branch |
| Load unresolved threads | GraphQL `reviewThreads(isResolved:false)` selecting node `id`, or MCP `get_review_comments` |
| Verify each thread | Read the referenced file's CURRENT content; check every requirement |
| Resolve (gh CLI) | `gh api graphql -f query='mutation($threadId:ID!){resolveReviewThread(input:{threadId:$threadId}){thread{id isResolved}}}' -F threadId='PRRT_...'` |
| Resolve (MCP) | `pull_request_review_write` with `method: "resolve_thread"`, `threadId: "PRRT_..."` |

**How It Works**

1. Verify available tooling (GitHub CLI and/or GitHub MCP).
2. Resolve the target PR (explicit argument wins over the current branch's PR).
3. Load only unresolved threads, capturing each thread's GraphQL node `id`.
4. For each thread, read the referenced file's current content and judge whether every requirement is satisfied (committed or uncommitted). Be critical — when unsure, leave it unresolved.
5. Resolve only FIXED/OBSOLETE threads via the `resolveReviewThread` mutation or the MCP `resolve_thread` method.
6. Report what was resolved and what was left unresolved, with reasons.
