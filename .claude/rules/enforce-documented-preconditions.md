---
title: Enforce a Documented Precondition in Code, or Do Not Claim It
paths:
  - "**/*.py"
---

# Enforce a Documented Precondition in Code, or Do Not Claim It

When a docstring asserts that some input combination cannot happen, the function
itself must make that true — with a guard, or by keeping the guard clause that
already made it true above the branch that depends on it. Reordering a rule to
the top of a chain and then explaining in prose why the skipped guards do not
matter leaves a public function that silently returns the wrong answer, and a
comment that a reader will trust instead of testing.

## Incorrect

`resolved` is hoisted above the `has_trial_result` guard, and the docstring
argues the combination is unreachable because *one particular caller* derives
the arguments consistently. Nothing enforces that, and nothing tests it.

```python
def verdict_from_signals(*, has_trial_result: bool, resolved: bool, ...) -> Verdict:
    """...
    `resolved` can only be true for a trial that produced a result.json, so
    rule 1 standing above rule 2 cannot claim a success for a trial that
    never ran.
    """
    if resolved:                      # a direct caller passing
        return Verdict(SUCCESS, "resolved")   # has_trial_result=False,
    if not has_trial_result:                  # resolved=True gets SUCCESS
        return Verdict(TECHNICAL_FAILURE, NO_TRIAL_RESULT_REASON)
```

## Correct

Move the rule only as far as it needs to go, so the guard it depends on still
runs first. The prose then describes what the code does instead of excusing it.

```python
def verdict_from_signals(*, has_trial_result: bool, resolved: bool, ...) -> Verdict:
    """...
    2. The verifier says resolved -- a solve, full stop. Checked BEFORE
       `exception_info` because a solved trial killed by a tail 429 is still
       a solve, and AFTER `has_trial_result` because a trial that never ran
       cannot have been solved.
    """
    if not has_trial_result:
        return Verdict(TECHNICAL_FAILURE, NO_TRIAL_RESULT_REASON)
    if resolved:
        return Verdict(SUCCESS, "resolved")
```

If the rule genuinely must sit at the top, add the guard to it
(`if resolved and has_trial_result:`) and pin the rejected combination with a
test. Either way the invariant lives in the code, not only in the docstring.

## Reference

- `.claude/rules/refactor-cross-references.md` — the companion rule for
  renumbering every derived restatement after a reorder.
