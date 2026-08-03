---
title: Update All Cross-References When Refactoring Numbered Sequences
impact: HIGH
---

# Update All Cross-References When Refactoring Numbered Sequences

When removing or renumbering a numbered element (gate, step, section, list item), **or introducing a numeric bound that tightens an existing one** (a new floor, cap, or threshold), grep the ENTIRE file for ALL derived references to the old range/count — not just the obvious primary block — and update every cross-reference. Adjacent checklists, legends, template comments, and action items often restate the old, looser range and become silently inconsistent.

## Incorrect

After removing Gate 7 from a Decision Gates table, the agent updates the primary algorithm range and criticality annotation but leaves checklist/comment cross-references pointing at the obsolete count.

```markdown
## Decision Gates
| Gate | ... |
| 0 ... | ... |
| 1 ... | ... |
... (Gate 7 row removed)
| 6 ... | ... |

```
for gate in [Gate 0, Gate 1, ..., Gate 6]:  # ← Updated
```

**Criticality Scale** (used by Gates 3 and 6):  # ← Updated

...later in the file...

<!-- Produced by Stage 5 (Decision Gates 0-7); render this block ONLY when ... -->  # ← MISSED
- [ ] Test Strategy designed with Decision Gates 0-7 walked  # ← MISSED
- [ ] All 8 gates evaluated explicitly  # ← MISSED
```

## Correct

After the primary removal, run a search for every numeric reference to the old range/count (e.g., `0-7`, `8 gates`, `Gates X, Y, Z`) across the entire file. Update every match.

```markdown
## Decision Gates
| Gate | ... |
... (Gate 7 row removed)
| 6 ... | ... |

```
for gate in [Gate 0, Gate 1, ..., Gate 6]:
```

**Criticality Scale** (used by Gates 3 and 6):

...later in the file...

<!-- Produced by Stage 5 (Decision Gates 0-6); render this block ONLY when ... -->  # ← Updated
- [ ] Test Strategy designed with Decision Gates 0-6 walked  # ← Updated
- [ ] All 7 gates evaluated explicitly  # ← Updated
```

After the edit, verify with: `grep -nE "0-7|8 gates|Gate 7" <file>` returns zero hits (except sanctioned exceptions explicitly noted).
