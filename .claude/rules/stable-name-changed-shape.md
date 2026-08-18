---
title: A Preserved Name Does Not Preserve the Contract
impact: HIGH
paths:
  - "plugins/**/*.md"
  - ".claude/agents/**/*.md"
  - ".claude/skills/**/*.md"
---

# A Preserved Name Does Not Preserve the Contract

When you change the SHAPE of a block but deliberately keep its NAME so consumers can still locate
it, grep those consumers for assertions about the BODY, not just for lookups of the name. A consumer
that validates the old shape under the stable name does not fail loudly — it silently rejects every
correct artifact the new shape produces. Report each shape-asserting consumer even when editing it
belongs to a later step.

## Incorrect

The author grepped for the heading, found the consumers, and concluded that keeping the name kept
them working — so only the name-lookup half of the finding was reported.

```markdown
<!-- Kept `**Rubric Score Definitions:**` verbatim: 6 files locate the sub-block by this string. -->

<!-- consumer, NOT inspected past the name match: -->
- Does `**Rubric Score Definitions:**` define 1-5 bins for EVERY criterion, measurably?
```

## Correct

Split the grep hits into name lookups (safe) and body predicates (broken), and report the second
list with file:line.

```markdown
<!-- Kept `**Rubric Score Definitions:**` verbatim: 6 files locate the sub-block by this string. -->

<!-- Name lookups — unaffected: developer.md:47, implement-task/SKILL.md:1603, README.md:91 -->
<!-- BODY PREDICATES — now reject conformant output, must be swept:
     plan-task/SKILL.md:784 gates on "1-5 bins for EVERY criterion"
     plan-task/SKILL.md:752 describes "one ### section per criterion with 1-5 bins" -->
```

## Reference

- `.claude/rules/dispatch-site-sweep.md` — the companion sweep for when the name itself changes.
