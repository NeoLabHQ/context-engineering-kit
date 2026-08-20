# /test-skill - Skill Pressure Testing

Verify skills work under pressure and resist rationalization using the RED-GREEN-REFACTOR cycle. Critical for discipline-enforcing skills.

- Purpose - Test skill effectiveness with pressure scenarios
- Output - Verification report with rationalization table

```bash
/test-skill ["skill path or name"]
```

## Usage Examples

```bash
# Test a TDD enforcement skill
> /test-skill tdd

# Test a custom skill by path
> /test-skill ~/.claude/skills/code-review/

# Start testing workflow
> /test-skill
```

## Arguments

Optional path to skill being tested or skill name.

## How It Works

1. **RED Phase - Baseline Testing**: Run scenarios WITHOUT the skill
   - Create pressure scenarios (3+ combined pressures)
   - Document agent behavior and rationalizations verbatim
   - Identify patterns in failures

2. **GREEN Phase - Write Minimal Skill**: Address baseline failures
   - Write skill addressing specific observed rationalizations
   - Run same scenarios WITH skill
   - Verify agent now complies

3. **REFACTOR Phase - Close Loopholes**: Iterate until bulletproof
   - Identify NEW rationalizations from testing
   - Add explicit counters for each loophole
   - Build rationalization table
   - Create red flags list
   - Re-test until bulletproof

## Pressure Types

| Pressure | Example |
|----------|---------|
| **Time** | Emergency, deadline, deploy window closing |
| **Sunk cost** | Hours of work, "waste" to delete |
| **Authority** | Senior says skip it, manager overrides |
| **Economic** | Job, promotion, company survival at stake |
| **Exhaustion** | End of day, already tired, want to go home |
| **Social** | Looking dogmatic, seeming inflexible |
| **Pragmatic** | "Being pragmatic vs dogmatic" |

## Best Practices

- Combine 3+ pressures - Single pressure tests are too weak
- Document verbatim - Capture exact rationalizations, not summaries
- Iterate completely - Continue REFACTOR until no new rationalizations
- Use meta-testing - Ask agents how skill could have been clearer
- Test all skill types - Discipline-enforcing, technique, pattern, and reference skills need different tests
