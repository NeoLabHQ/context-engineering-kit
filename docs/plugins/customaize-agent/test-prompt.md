# /test-prompt - Prompt Testing with Subagents

Test any prompt (commands, hooks, skills, subagent instructions) using the RED-GREEN-REFACTOR cycle with subagents for isolated testing.

- Purpose - Verify prompts produce desired behavior before deployment
- Output - Test results with improvement recommendations

```bash
/test-prompt ["prompt path or content"]
```

## Usage Examples

```bash
# Test a command before deployment
> /test-prompt .claude/commands/deploy.md

# Test inline prompt content
> /test-prompt "Review this code for security issues"

# Start interactive testing workflow
> /test-prompt
```

## Arguments

Optional path to prompt file or inline prompt content to test.

## How It Works

1. **RED Phase - Baseline Testing**: Run without prompt using subagent
   - Design test scenarios appropriate for prompt type
   - Launch subagent WITHOUT prompt
   - Document agent behavior, actions, and mistakes

2. **GREEN Phase - Write Minimal Prompt**: Make tests pass
   - Address specific baseline failures
   - Apply appropriate degrees of freedom
   - Use persuasion principles if discipline-enforcing
   - Test WITH prompt using subagent

3. **REFACTOR Phase - Optimize**: Improve while staying green
   - Close loopholes for discipline violations
   - Improve clarity using meta-testing
   - Reduce tokens without losing behavior
   - Re-test with fresh subagents

## Why Subagents?

| Benefit | Description |
|---------|-------------|
| **Clean slate** | No conversation history affecting behavior |
| **Isolation** | Test only the prompt, not accumulated context |
| **Reproducibility** | Same starting conditions every run |
| **Parallelization** | Test multiple scenarios simultaneously |
| **Objectivity** | No bias from prior interactions |

## Prompt Types & Testing Strategies

| Prompt Type | Test Focus | Example |
|-------------|------------|---------|
| **Instruction** | Steps followed correctly? | Git workflow command |
| **Discipline-enforcing** | Resists rationalization? | TDD compliance skill |
| **Guidance** | Applied appropriately? | Architecture patterns |
| **Reference** | Accurate and accessible? | API documentation |
| **Subagent** | Task accomplished reliably? | Code review prompt |

## Best Practices

- Use fresh subagents - Always via Task tool for isolated testing
- Design realistic scenarios - Include constraints, pressures, edge cases
- Document exact failures - "Agent was wrong" doesn't tell you what to fix
- Avoid over-engineering - Only address failures you documented in baseline
- Iterate on token efficiency - Reduce tokens without losing behavior
