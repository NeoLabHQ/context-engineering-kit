# /code-review:review-local-changes - Local Changes Review

Review uncommitted local changes using all specialized agents with code improvement suggestions.

- Purpose - Comprehensive review before committing
- Output - Structured report with findings by severity

```bash
/code-review:review-local-changes [review-aspects] [--min-impact critical|high|medium|medium-low|low] [--json]
```

## Arguments

| Argument | Format | Default | Description |
|----------|--------|---------|-------------|
| `review-aspects` | Free text | None | Optional review aspects or focus areas (e.g., "security, performance") |
| `--min-impact` | `--min-impact <level>` | `high` | Minimum impact level for reported issues. Values: `critical`, `high`, `medium`, `medium-low`, `low` |
| `--json` | Flag | `false` | Output results in JSON format instead of markdown |

### Impact Level Mapping

| Level | Impact Score Range |
|-------|-------------------|
| `critical` | 81-100 |
| `high` | 61-80 |
| `medium` | 41-60 |
| `medium-low` | 21-40 |
| `low` | 0-20 |

## How It Works

1. **Change Detection**: Identifies all uncommitted changes in the working directory
   - Staged changes
   - Unstaged modifications
   - New files

2. **Parallel Agent Analysis**: Spawns six specialized agents simultaneously
   - Bug Hunter - Identifies potential bugs and edge cases
   - Security Auditor - Finds security vulnerabilities
   - Test Coverage Reviewer - Evaluates test coverage
   - Code Quality Reviewer - Assesses code structure
   - Contracts Reviewer - Reviews API contracts
   - Historical Context Reviewer - Analyzes codebase patterns

3. **Finding Aggregation**: Combines all agent reports
   - Categorizes by severity (Critical, High, Medium, Medium-Low, Low)
   - Scores each issue for confidence (is it real?) and impact (how severe?)
   - Removes duplicates
   - Adds file and line references

4. **Filtering**: Applies two sequential filters to reduce noise
   - **Min-impact cutoff** - Excludes issues below the `--min-impact` threshold (default: `high`, score 61+)
   - **Progressive confidence threshold** - Higher-impact issues require less confidence to pass (Critical: 50%, High: 65%, Medium: 75%, Medium-Low: 85%, Low: 95%)

5. **Report Generation**: Produces actionable report in markdown (default) or JSON (`--json`) format with prioritized findings

## Usage Examples

```bash
# Review all local changes (default: --min-impact high, markdown output)
> /code-review:review-local-changes

# Focus on security aspects
> /code-review:review-local-changes security

# Lower the threshold to catch medium-impact issues
> /code-review:review-local-changes --min-impact medium

# Focus on security and performance, medium threshold
> /code-review:review-local-changes security, performance --min-impact medium

# Critical-only issues in JSON for programmatic consumption
> /code-review:review-local-changes --min-impact critical --json

# After implementing a feature
> claude "implement user authentication"
> /code-review:review-local-changes
```

### JSON Output

When using `--json`, the output is a structured object with these top-level fields:

- `quality_gate` - `"PASS"` or `"FAIL"` (fails when any critical or high issue exists)
- `summary` - Issue counts by severity
- `issues` - Array of issues with `severity`, `file`, `lines`, `description`, `evidence`, `impact_score`, `confidence_score`, and optional `suggestion`
- `improvements` - Array of code improvement suggestions from the code-quality-reviewer agent

## Best Practices

- Review before committing - Run review on local changes before `git commit`
- Address critical issues first - Fix Critical and High priority findings immediately
- Iterate after fixes - Run again to verify issues are resolved
- Combine with reflexion - Use `/reflexion:memorize` to save patterns for future reference
