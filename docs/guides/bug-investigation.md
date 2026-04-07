# Bug Investigation and Fix

Systematic bug fixing with root cause analysis using Kaizen methodology to eliminate problems at their source.

For simple, obvious bugs (typos, single-line fixes), use [Feature Development](./feature-development.md) workflow.

## When to Use

- Bugs with unclear root cause requiring investigation
- Recurring issues that need systematic analysis
- Production incidents requiring post-mortem
- Complex bugs spanning multiple components

## Plugins needed for this workflow

- [Git](../plugins/git/README.md)
- [Kaizen](../plugins/kaizen/README.md)
- [Code Review](../plugins/code-review/README.md)
- [Reflexion](../plugins/reflexion/README.md)

## Workflow

### How It Works

```md
┌─────────────────────────────────────────────┐
│ 1. Load Issue Context                       │
│    (analyze GitHub issue)                   │
└────────────────────┬────────────────────────┘
                     │
                     │ understand symptoms and reproduction steps
                     ▼
┌─────────────────────────────────────────────┐
│ 2. Trace Root Cause                         │
│    (trace through call stack)               │
└────────────────────┬────────────────────────┘
                     │
                     │ identify source of invalid data or behavior
                     ▼
┌─────────────────────────────────────────────┐
│ 3. Analyze with Five Whys                   │
│    (drill from symptoms to fundamentals)    │
└────────────────────┬────────────────────────┘
                     │
                     │ understand why the bug exists
                     ▼
┌─────────────────────────────────────────────┐
│ 4. Implement Fix                            │
│    (address root cause, not symptoms)       │
└────────────────────┬────────────────────────┘
                     │
                     │ verify fix addresses the root cause
                     ▼
┌─────────────────────────────────────────────┐
│ 5. Review Fix                               │
│    (multi-agent code review)                │
└────────────────────┬────────────────────────┘
                     │
                     │ ensure fix doesn't introduce new issues
                     ▼
┌─────────────────────────────────────────────┐
│ 6. Preserve Learnings                       │
│    (update project memory)                  │
└────────────────────┬────────────────────────┘
                     │
                     │ prevent similar bugs in future
                     ▼
┌─────────────────────────────────────────────┐
│ 7. Commit with Context                      │
│    (conventional commit with issue link)    │
└─────────────────────────────────────────────┘
```

### 1. Load issue context

Use the `/git:analyze-issue` command to load the bug report from GitHub and extract technical details.

```bash
/git:analyze-issue #123
```

After LLM completes, you will have a structured understanding of the bug symptoms, reproduction steps, affected areas, and any related issues or context from the discussion.

### 2. Trace root cause

Use the `/root-cause-tracing` command to systematically trace the bug backward through the call stack.

```bash
/root-cause-tracing
```

After LLM completes, you will have identified where invalid data originates or where incorrect behavior starts. This traces from the symptom (e.g., wrong output) back to the source (e.g., missing validation in input handler).

### 3. Analyze with Five Whys

Use the `/why` command to drill deeper into why the root cause exists in the first place.

```bash
/why
```

After LLM completes, you will understand not just what went wrong, but why the codebase allowed it to happen. This reveals systemic issues like missing tests, unclear specifications, or architectural gaps that enabled the bug.

### 4. Implement fix

With a clear understanding of the root cause and its underlying reasons, implement a fix that addresses the fundamental issue.

```bash
Fix the rate limiting bug by adding proper Redis locking based on root cause analysis
```

After LLM completes, verify the fix addresses the actual root cause identified in steps 2-3, not just the surface symptoms. A proper fix should prevent the entire class of similar bugs, not just this specific instance.

**Tip**: Add "reflect" to your prompt for automatic verification of the fix:

```bash
Fix the rate limiting bug by adding proper Redis locking based on root cause analysis, then reflect
```

Claude will implement the fix and automatically review it for correctness.

### 5. Review fix

Use the `/review-local-changes` command to ensure the fix is correct and doesn't introduce new issues.

```bash
/review-local-changes
```

After LLM completes, address any findings from the multi-agent review. Pay special attention to Bug Hunter findings (new edge cases) and Test Coverage (ensuring the bug has regression tests).

### 6. Preserve learnings

Use the `/reflexion:memorize` command to capture insights from this bug investigation for future reference.

```bash
/reflexion:memorize Bug pattern: race conditions in Redis operations
```

After LLM completes, your CLAUDE.md will be updated with learnings about this bug pattern, helping prevent similar issues in future development. This builds institutional knowledge about your codebase's pitfalls.

### 7. Commit with context

Use the `/git:commit` command to create a well-documented commit that links to the issue and explains the fix.

```bash
/git:commit
```

After LLM completes, your commit will follow conventional commit format with the bug fix type, proper scope, and reference to the issue (e.g., `Fixes #123`). This creates a searchable history for future debugging.

## Alternative Analysis Methods

The Kaizen plugin offers additional analysis techniques for different scenarios:

### For complex, multi-factor bugs

Use Fishbone (Cause-and-Effect) analysis to explore causes across six categories:

```bash
/cause-and-effect
```

### For comprehensive problem documentation

Use A3 analysis for a one-page problem summary with root cause and action plan:

```bash
/analyse-problem
```

### For iterative experimentation

Use PDCA (Plan-Do-Check-Act) cycle when the fix requires testing hypotheses:

```bash
/plan-do-check-act
```
