---
title: Verify a Referenced Source Exists Before Instructing an Agent to Read It
impact: HIGH
paths:
  - "plugins/**/*.md"
  - ".claude/agents/**/*.md"
  - ".claude/skills/**/*.md"
---

# Verify a Referenced Source Exists Before Instructing an Agent to Read It

When an instruction tells an agent to take a value from a named file, section, or field, first open
the producer of that format and confirm it actually emits that value. An instruction pointing at a
source that never exists leaves the agent with no defined behaviour — worse than stating no rule at
all, because it suppresses the fallback that would otherwise apply. This is especially easy to get
wrong when porting a pattern from a reference implementation: port its structure, never its
assumptions about what the input contains.

## Incorrect

A fallback clause invents a config source by symmetry with a neighbouring one. Sub-task files are
produced by `plugins/sdd/agents/tech-lead.md`, whose template emits `#### Expected Output`,
`#### Success Criteria`, `#### Subtasks` and `#### Blockers & Risks` — there is no
`#### Verification` block at all, so the no-override path resolves to nothing.

```markdown
- **Model**: `MODEL_OVERRIDE` if set — otherwise the step's `Model` column — otherwise `sonnet`

**Reviewer** — dispatch with **Model**: `MODEL_OVERRIDE` if set
  — otherwise as specified in the step's `#### Verification`
```

## Correct

Grep the producer first (`grep -n '#### Verification' plugins/sdd/agents/tech-lead.md` → no hits),
then terminate the chain with a source that always resolves.

```markdown
- **Model**: `MODEL_OVERRIDE` if set — otherwise the step's `Model` column — otherwise `sonnet`

**Reviewer** — dispatch with **Model**: `MODEL_OVERRIDE` if set
  — otherwise the phase's `Reviewer model` from the Phase Overview
```

## Reference

- `.claude/rules/refactor-cross-references.md` — the companion check for references that were once
  valid and went stale.
