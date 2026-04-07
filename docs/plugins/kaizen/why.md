# /why - Five Whys Root Cause Analysis

Iterative questioning technique that drills from surface symptoms to fundamental root causes by repeatedly asking "why."

- Purpose - Find the true root cause, not just symptoms
- Output - Chain of causation leading to actionable root cause

```bash
/why ["issue or symptom description"]
```

## Arguments

Optional description of the issue or symptom to analyze. If not provided, you will be prompted for input.

## How It Works

1. **State the Problem**: Clearly define the observable symptom or issue
2. **First Why**: Ask why this problem occurs; document the immediate cause
3. **Iterate**: For each answer, ask "why" again to go deeper
4. **Branch When Needed**: If multiple causes emerge, explore each branch separately
5. **Identify Root Cause**: Usually reached after 5 iterations when you hit systemic/process issues
6. **Validate**: Work backwards from root cause to symptom to verify the chain
7. **Propose Solutions**: Address root causes, not symptoms

### Depth Guidelines

- **Stop when**: You reach process, policy, or systemic issues
- **Keep going if**: "Human error" appears (ask why error was possible)
- **Branch when**: Multiple contributing factors exist
- **Not always 5**: Stop at true root cause, whether 3 or 7 whys deep

## Usage Examples

```bash
# Investigate a production bug
> /why "Users see 500 error on checkout"

# Analyze a recurring issue
> /why "E2E tests fail intermittently"

# Understand a performance problem
> /why "Feature deployment takes 2 hours"
```

### Example Output

```
Problem: Users see 500 error on checkout
Why 1: Payment service throws exception
Why 2: Request timeout after 30 seconds
Why 3: Database query takes 45 seconds
Why 4: Missing index on transactions table
Why 5: Index creation wasn't in migration scripts

Root Cause: Migration review process doesn't check query performance
Solution: Add query performance checks to migration PR template
```

## Best Practices

- Do not stop at symptoms - Keep asking "why" until you reach systemic causes
- Explore multiple branches - Complex problems often have multiple contributing factors
- Avoid blame - Focus on process and systems, not individuals
- Document everything - The chain of causation is valuable for future reference
- Test solutions - Implement, verify the symptom is resolved, then monitor for recurrence
