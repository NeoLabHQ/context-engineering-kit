# /code-review:review-pr - Pull Request Review

Comprehensive pull request review using all specialized agents. Posts only high-confidence, high-value inline comments directly on PR lines - no overall review report.

- Purpose - Review PR changes before merge with minimal noise
- Output - Inline comments on specific lines (only issues that pass confidence/impact thresholds)

```bash
/code-review:review-pr [review-aspects] [--min-impact critical|high|medium|medium-low|low]
```

## CI/CD Integration

You can integrate this plugin with your CI/CD pipeline by using Offical Anthropics Claude Code Action. See [CI/CD Integration](../../guides/ci-integration.md) for more details.

## Arguments

| Argument | Format | Default | Description |
|----------|--------|---------|-------------|
| `review-aspects` | Free text | None | Optional review aspects or focus areas (e.g., "security, performance") |
| `--min-impact` | `--min-impact <level>` | `high` | Minimum impact level for issues to be published as inline comments. Values: `critical`, `high`, `medium`, `medium-low`, `low` |

### Impact Level Mapping

| Level | Impact Score Range |
|-------|-------------------|
| `critical` | 81-100 |
| `high` | 61-80 |
| `medium` | 41-60 |
| `medium-low` | 21-40 |
| `low` | 0-20 |

## How It Works

1. **PR Context Loading**: Fetches PR details and diff
   - Changed files
   - Commit messages
   - PR description
   - Base branch context

2. **Parallel Agent Analysis**: Same six agents analyze the PR diff
   - Each agent examines changes from their specialty perspective
   - Considers PR context and commit messages

3. **Confidence & Impact Scoring**: Each issue is scored on two dimensions
   - **Confidence (0-100)**: How likely is this a real issue vs false positive?
   - **Impact (0-100)**: How severe is the consequence if left unfixed?
   - Progressive threshold: Critical issues (81-100 impact) need 50% confidence, Low issues (0-20 impact) need 95% confidence

4. **Inline Comment Posting**: Only issues passing both filters get posted
   - Issues below the `--min-impact` level (default: `high` / score 61+) are excluded
   - Issues below the progressive confidence threshold for their impact level are excluded
   - Uses GitHub inline comments on specific PR lines


## Usage Examples

```bash
# Review PR by number
> /code-review:review-pr #123

# Review PR with focus on security
> /code-review:review-pr security

# Include medium-impact issues and above
> /code-review:review-pr --min-impact medium

# Combine focus areas with a lower impact threshold
> /code-review:review-pr security, performance --min-impact medium-low

# Review current branch's PR (defaults to --min-impact high)
> /code-review:review-pr
```


