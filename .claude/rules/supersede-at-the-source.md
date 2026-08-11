---
title: Delete a Superseded Instruction at Its Source, Not With a Downstream Override
impact: HIGH
paths:
  - "plugins/**/*.md"
  - ".claude/agents/**/*.md"
  - ".claude/skills/**/*.md"
---

# Delete a Superseded Instruction at Its Source, Not With a Downstream Override

When a refactor removes an output contract, template, or stage that lives in a file another prompt
dispatches ("read X and execute it exactly as written"), edit or delete it in that file. Layering a
prose override on top leaves two live, contradicting contracts in the same execution surface, and
which one the model follows becomes a coin flip that depends on attention, not on the spec.

## Incorrect

The dispatching agent keeps the old template alive and tries to suppress it with prose.

```markdown
**MANDATORY**: Read `skills/plan-task/analyse-business-requirements.md` and execute its
STAGES 2-5 in full, exactly as written.

**Override:** Its STAGE 6 is SUPERSEDED. Do NOT emit its `### Functional Requirements` /
`### Non-Functional Requirements` template into the task file.
```

```markdown
<!-- analyse-business-requirements.md — UNCHANGED, still a live task-file write -->
### STAGE 6: Update Task File
Use Write tool to update the task file.
## Acceptance Criteria
### Functional Requirements
- [ ] **[Criterion 1]**: ...
```

## Correct

Remove the superseded stage from the source file so exactly one contract exists.

```markdown
**MANDATORY**: Read `skills/plan-task/analyse-business-requirements.md` and execute its
STAGES 2-5 in full, exactly as written. It writes only to the scratchpad.
```

```markdown
<!-- analyse-business-requirements.md — STAGE 6 deleted; the dispatching agent owns the write -->
### STAGE 5: Synthesis
[...writes Phase 4 to the scratchpad...]
```

## Reference

- `.claude/rules/grounded-instruction-references.md` — the companion check for references pointing at
  a source that produces nothing.
