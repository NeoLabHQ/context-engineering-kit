---
title: A Verbatim Move Preserves Block Form, Including Blocks That Look Redundant
paths:
  - "plugins/**/*.md"
  - ".claude/agents/**/*.md"
  - ".claude/rules/**/*.md"
---

# A Verbatim Move Preserves Block Form, Including Blocks That Look Redundant

When an instruction says to move or inline content **without summarising or rephrasing**, copy every
block in its original form — tables stay tables, fences stay fences — even when a block restates
something already stated elsewhere in the destination. Judging a block redundant and folding it into
prose is an edit, not a move: it changes what a reader scanning for a table will find, and it hides
inside a diff that otherwise looks like a faithful transplant. If a block really is duplicated,
report the duplication and let the reviewer decide; do not resolve it inside the move.

## Incorrect

The source's output-contract table is judged redundant with a richer table earlier in the host file,
so its four rows are folded into one sentence. The words survive; the table does not.

```markdown
<!-- source -->
| Scratchpad section | Produced by |
|--------------------|-------------|
| `## Phase 1: Requirements Discovery` | STAGE 1 |
| `## Phase 2: Concept Extraction` | STAGE 2 |
| `## Phase 3: Requirements Analysis` (incl. the Acceptance Criteria Draft) | STAGE 3 |
| `## Phase 4: Draft Output` (refined description, scope summary) | STAGE 4 |

<!-- after the "move" -->
MUST contain every section of the sub-step table above: `## Phase 1: Requirements Discovery` (2.1),
`## Phase 2: Concept Extraction` (2.2), `## Phase 3: Requirements Analysis` incl. the Acceptance
Criteria Draft (2.3), and `## Phase 4: Draft Output` — refined description, scope summary (2.4).
```

## Correct

The table is copied as a table; only the stage identifiers are re-anchored to the host's numbering.

```markdown
MUST contain:

| Scratchpad section | Produced by |
|--------------------|-------------|
| `## Phase 1: Requirements Discovery` | 2.1 |
| `## Phase 2: Concept Extraction` | 2.2 |
| `## Phase 3: Requirements Analysis` (incl. the Acceptance Criteria Draft) | 2.3 |
| `## Phase 4: Draft Output` (refined description, scope summary) | 2.4 |
```

## Reference

- `.claude/rules/scope-bounded-token-budget.md` — the companion rule for content outside the change.
- Verify a move with counts, not impressions: compare fences, table rows and headings against the
  pre-change file and account for every shortfall.
