# /cause-and-effect - Fishbone Analysis

Systematic exploration of problem causes across six categories using the Ishikawa (Fishbone) diagram approach.

- Purpose - Comprehensive multi-factor root cause exploration
- Output - Structured analysis across People, Process, Technology, Environment, Methods, and Materials

```bash
/cause-and-effect ["problem description"]
```

## Arguments

Optional problem description to analyze. If not provided, you will be prompted for input.

## How It Works

1. **State the Problem**: Define the "head" of the fish - the effect you're analyzing
2. **Explore Each Category**: Brainstorm potential causes in six domains:
   - **People**: Skills, training, communication, team dynamics
   - **Process**: Workflows, procedures, standards, reviews
   - **Technology**: Tools, infrastructure, dependencies, configuration
   - **Environment**: Workspace, deployment targets, external factors
   - **Methods**: Approaches, patterns, architectures, practices
   - **Materials**: Data, dependencies, third-party services, resources
3. **Dig Deeper**: For each potential cause, ask "why" to uncover deeper issues
4. **Identify Root Causes**: Distinguish contributing factors from fundamental causes
5. **Prioritize**: Rank causes by impact and likelihood
6. **Propose Solutions**: Address highest-priority root causes

## Usage Examples

```bash
# Analyze performance issues
> /cause-and-effect "API responses take 3+ seconds"

# Investigate test reliability
> /cause-and-effect "15% of test runs fail, passing on retry"

# Understand delivery delays
> /cause-and-effect "Feature took 12 weeks instead of 3"
```

### Example Output

```
Problem: API responses take 3+ seconds (target: <500ms)

PEOPLE
├─ Team unfamiliar with performance optimization
├─ No one owns performance monitoring
└─ Frontend team doesn't understand backend constraints

PROCESS
├─ No performance testing in CI/CD
├─ No SLA defined for response times
└─ Performance regression not caught in code review

TECHNOLOGY
├─ Database queries not optimized
│  └─ Why: No query analysis tools in place
├─ N+1 queries in ORM
│  └─ Why: Eager loading not configured
└─ No caching layer

ROOT CAUSES:
- No performance requirements defined (Process)
- Missing performance monitoring tooling (Technology)
- Architecture doesn't support caching/async (Methods)

SOLUTIONS (Priority Order):
1. Add database indexes (quick win, high impact)
2. Implement Redis caching layer (medium effort, high impact)
3. Define and monitor performance SLAs (low effort, prevents regression)
```

## Best practices

- Do not stop at first cause - Explore deeply within each category
- Look for cross-category connections - Some causes span multiple domains
- Root causes usually involve process or methods - Not just technology
- Combine with /why - Use Five Whys to dig deeper on specific causes
- Prioritize by impact x feasibility / effort - Focus on highest-value fixes
