# /git:load-pr-comments - Load Unresolved PR Comments

Load open/unresolved PR review comments and rewrite them as grouped, independently-implementable markdown tasks for parallel agents to fix.

- Purpose - Turn unresolved PR review feedback into focused, conflict-free task files
- Output - Grouped task-oriented markdown files under `.specs/comments/*.md`

```bash
/git:load-pr-comments [pr-number-or-url]
```

## Arguments

| Argument | Format | Default | Description |
|----------|--------|---------|-------------|
| `pr-number-or-url` | Number or URL | Current branch's PR | Optional PR number (e.g. `123`) or full URL (e.g. `https://github.com/owner/repo/pull/123`). When omitted, the command targets the PR associated with the current git branch. |

An explicit PR argument always takes precedence over current-branch resolution. If no PR exists for the current branch and no argument is given, the command stops and asks for a PR number or URL.

## How It Works

1. **Tool Detection**: Checks whether GitHub CLI (`gh auth status`) and/or the GitHub MCP server are available, selecting whichever has repository access.
2. **PR Resolution**: Uses the PR number/URL argument if provided (extracting the number after `/pull/`), otherwise resolves the current branch's PR via `gh pr view`.
3. **Unresolved Thread Retrieval**: Fetches review threads via the. This is read-only - nothing is posted, replied to, or modified on GitHub.
4. **Group and Rewrite as Tasks**: Deduplicates identical/overlapping threads, then rewrites each unresolved comment as an actionable task requirement (preserving code suggestions and exact wording verbatim, dropping conversation framing). Human reviewer feedback is preferred over bot/AI suggestions when both exist.
5. **.gitignore Handling**: Idempotently ensures `.specs/comments/*.md` is present in `.gitignore`, creating the file if needed.
6. **Write Files**: Writes grouped tasks to `.specs/comments/<kebab-topic>.md`, grouping by file or functionality so no two files overlap, aggregating trivial nitpicks into a single combined file, and capping at 5 files total.
7. **Report**: Summarizes the target PR, count of unresolved threads loaded, files created with their topics, and any threads skipped (resolved) or limitations hit.

## Usage Examples

```bash
# Load unresolved comments for the current branch's PR
> /load-pr-comments

# Load by PR number
> /load-pr-comments 123

# Load by PR URL
> /load-pr-comments https://github.com/owner/repo/pull/123
```

## Artifacts Generated

```text
.specs/
└── comments/
    ├── <kebab-topic>.md    # Focused, independently-implementable task group
    └── nitpicks.md         # Aggregated trivial one-line changes
```

## Best Practices

- Resolve before reloading - Mark addressed threads resolved on GitHub so reruns surface only outstanding feedback.
- Fix in parallel - Each generated file is conflict-free and independently implementable, so dispatch a separate agent per file.
- Keep groups focused - Files are capped at 5; unrelated changes stay in separate files rather than being over-combined.
- Pair with review - Combine with `/review-pr` to triage feedback before turning it into tasks.
