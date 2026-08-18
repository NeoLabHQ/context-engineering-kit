---
title: Narrow a Criteria Set Item-by-Item, Not Sub-Block-by-Sub-Block
impact: HIGH
---

# Narrow a Criteria Set Item-by-Item, Not Sub-Block-by-Sub-Block

When an evaluation contract is narrowed from whole-task scope to a checkpoint/milestone
scope, audit every INDIVIDUAL item of each carried-over sub-block for task-level phrasing
("every", "all", "no orphans"). A sub-block waved through wholesale with "applies at every
checkpoint" silently reintroduces the whole-task gate the narrowing was meant to remove,
and the checkpoint fails on work that is not yet due.

## Incorrect

The whole sub-block is admitted at every checkpoint, so its task-level completion items
(which can only be satisfied at the final checkpoint) become mandatory failures earlier.

```markdown
| `**Regular Checks:**` — build / lint / tests / duplication / reuse / test-coverage
  checkboxes | Apply to **every** phase. A failing gate is an essential-level failure |

<!-- but that list contains, verbatim: -->
- [ ] Every entry in the **Test Cases to Cover** list has an implemented test
- [ ] Every testable checklist item resolves to at least one real, passing test
```

## Correct

Split the sub-block by item scope and state which items are checkpoint-scoped and which
are deferred, at the site that admits them.

```markdown
| `**Regular Checks:**` | Per-checkpoint gates (build / lint / tests / duplication /
  reuse) apply at EVERY phase — a failing gate is an essential-level failure.
  The whole-task coverage gates ("Every entry in **Test Cases to Cover**...",
  "Every testable checklist item resolves...") are narrowed to the `#### CK-N:` groups
  THIS phase lists; unlisted groups are not yet due and never answer NO |
```

## Reference

- `.claude/rules/refactor-cross-references.md` — the companion sweep for derived references.
