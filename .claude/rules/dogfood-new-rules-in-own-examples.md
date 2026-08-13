---
title: Apply a Newly Added Rule to the File's Own Worked Examples
impact: HIGH
paths:
  - "plugins/**/agents/*.md"
  - "plugins/**/skills/**/*.md"
  - ".claude/agents/*.md"
---

# Apply a Newly Added Rule to the File's Own Worked Examples

After adding a constraint to a prompt or agent file, re-audit every worked example already in that
file against the new constraint and fix the ones that violate it. A model imitates the demonstration
far more reliably than it obeys the prose, so one self-contradicting example silently repeals the
rule it sits beside.

## Incorrect

A new rule demands the two anchors differ on exactly one thing, but the worked example further down
the same file was carried over unchanged and differs on two — status-code precision *and* body
assertion.

```yaml
# Rule added at the top of the file:
# "The two anchors MUST differ on exactly ONE thing."

  - name: "Assertion Quality"
    anchors:
      score_2: |
        expect(r.status).toBeLessThan(300);
      score_4: |
        expect(res.status).toBe(200);
        expect(res.body).toEqual([{ id: expect.any(String) }]);
      contrast: "score_4 asserts the exact status code and the exact response body; score_2 asserts only a status range."
```

## Correct

Hold one attribute fixed so the pair isolates the single difference the dimension names.

```yaml
  - name: "Assertion Quality"
    anchors:
      score_2: |
        expect(res.status).toBe(200);
      score_4: |
        expect(res.status).toBe(200);
        expect(res.body).toEqual([{ id: expect.any(String) }]);
      contrast: "score_4 asserts the response body as well; score_2 asserts only the status."
```

## Reference

- `.claude/rules/refactor-cross-references.md` — the companion sweep for derived references that go
  stale rather than contradict.
