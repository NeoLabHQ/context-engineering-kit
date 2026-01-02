# Reliable Engineering with Competitive Synthesis

High-assurance workflow for critical features using multi-agent competitive generation, independent evaluation, and evidence-based synthesis to produce superior solutions.

For simple features that don't require competitive exploration, use [Feature Development](./feature-development.md) workflow.

## When to Use

- **Quality-critical implementations** - Authentication, payment processing, data validation
- **Novel or ambiguous requirements** - No clear "right answer", multiple valid approaches
- **High-stakes architectural decisions** - API design, schema design, core algorithms
- **Avoiding local optima** - When single-agent reflection might miss better approaches

## When NOT to Use

- Simple, well-defined tasks with obvious solutions
- Time-sensitive changes where speed matters more than exploration
- Trivial bug fixes or typos
- Tasks with only one viable approach

## Plugins Needed

- [SADD](../plugins/sadd/README.md) - Competitive execution
- [TDD](../plugins/tdd/README.md) - Test coverage
- [Code Review](../plugins/code-review/README.md) - Final validation
- [Git](../plugins/git/README.md) - Version control

## Workflow

### How It Works

```md
                                    PHASE 1: COMPETITIVE GENERATION
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Task ───┬─ Agent 1 → Draft → Self-Critique → Revise → Solution A ─┐            │
│         ├─ Agent 2 → Draft → Self-Critique → Revise → Solution B ─┼─┐          │
│         └─ Agent 3 → Draft → Self-Critique → Revise → Solution C ─┘ │          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
                                    PHASE 2: MULTI-JUDGE EVALUATION
┌─────────────────────────────────────────────────────────────────────────────────┐
│         ┌─ Judge 1 → Evaluate → Verify → Report A ─┐                           │
│         ├─ Judge 2 → Evaluate → Verify → Report B ─┼─ Consensus Analysis       │
│         └─ Judge 3 → Evaluate → Verify → Report C ─┘                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
                                    PHASE 3: ADAPTIVE STRATEGY
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    Clear Winner? → SELECT_AND_POLISH                            │
│                    All Flawed?   → REDESIGN (restart Phase 1)                   │
│                    Split Vote?   → FULL_SYNTHESIS                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
                                    QUALITY GATES
┌─────────────────────────────────────────────────────────────────────────────────┐
│         Write Tests → Review Changes → Create Commit                            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Competitive Implementation

Use `/sadd:do-competitively` to generate multiple solutions, evaluate them independently, and synthesize the best elements.

```bash
/sadd:do-competitively "Implement JWT authentication middleware with token refresh, rate limiting, and secure session management"
```

**What happens:**
1. **3 agents** independently design and implement solutions with self-critique
2. **3 judges** evaluate each solution using structured rubrics with verification
3. **Adaptive strategy** selects: polish the winner, redesign if all flawed, or synthesize best elements

For specific output location:

```bash
/sadd:do-competitively "Design user authentication schema" --output "src/models/auth.ts"
```

With custom evaluation criteria:

```bash
/sadd:do-competitively "Create API rate limiting middleware" --criteria "security,performance,maintainability"
```

After completion, review the synthesized solution to ensure it meets your requirements.

### 2. Write Tests

Use `/tdd:write-tests` to generate comprehensive test coverage for the synthesized solution.

```bash
/tdd:write-tests
```

Or with specific focus:

```bash
/tdd:write-tests Focus on security edge cases and error handling
```

Verify all tests pass before continuing.

### 3. Review Local Changes

Use `/code-review:review-local-changes` for final multi-agent validation.

```bash
/code-review:review-local-changes
```

Address Critical and High priority findings before committing.

### 4. Create Commit

Use `/git:commit` to create a well-formatted conventional commit.

```bash
/git:commit
```

## Quality Comparison

| Aspect | Feature Development | Reliable Engineering |
|--------|---------------------|----------------------|
| **Agents** | 1 (with self-reflection) | 3 generators + 3 judges |
| **Exploration** | Single path | Multiple competing approaches |
| **Issue Detection** | 40-60% (self-critique) | 70-85% (competitive + judges) |
| **Cost** | Lower | 4-6x higher |
| **Time** | Faster | Slower |
| **Best For** | Simple, clear tasks | Critical, ambiguous tasks |

## Advanced: Combining with Tree of Thoughts

For tasks requiring exploration before commitment, use `/sadd:tree-of-thoughts` first:

```bash
# Explore approaches first
/sadd:tree-of-thoughts "Design caching strategy for high-traffic API"

# Then implement the winning approach competitively
/sadd:do-competitively "Implement Redis-based caching with the write-through pattern identified above"
```

## Advanced: Debate-Based Evaluation

For highest-stakes decisions where consensus is critical:

```bash
# Implement competitively
/sadd:do-competitively "Design payment processing flow" --output "src/services/payment.ts"

# Evaluate with iterative debate
/sadd:judge-with-debate --solution "src/services/payment.ts" --task "Payment processing implementation" --criteria "security:30,correctness:30,reliability:20,performance:20"
```

## Tips

- **Reserve for critical work** - The 4-6x cost overhead is only justified for high-stakes implementations
- **Specify criteria** - Custom evaluation criteria improve judge alignment with your priorities
- **Review synthesis** - Always validate the final synthesized solution makes coherent sense
- **Iterate if needed** - If REDESIGN strategy triggers, provide more context on second attempt
- **Use for learning** - Competitive execution reveals trade-offs between approaches

## Theoretical Foundation

This workflow combines research-backed techniques:

| Technique | Source | Benefit |
|-----------|--------|---------|
| Constitutional AI Self-Critique | Bai et al., 2022 | 40-60% issue reduction before review |
| Chain of Verification | Dhuliawala et al., 2023 | Reduces judge bias |
| Multi-Agent Debate | Du et al., 2023 | Diverse perspectives improve reasoning |
| Self-Consistency | Wang et al., 2022 | Multiple paths improve reliability |
