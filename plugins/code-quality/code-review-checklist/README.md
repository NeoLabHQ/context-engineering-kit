# Code Review Checklist Plugin

A systematic code review checklist that ensures comprehensive quality checks without missing critical issues.

## Purpose

Provides a structured approach to code review that covers:
- Correctness and logic errors
- Security vulnerabilities
- Performance issues
- Maintainability concerns
- Test coverage

## Installation

1. Copy this plugin directory to your Claude Code plugins folder:
```bash
cp -r code-review-checklist ~/.claude-code/plugins/
```

2. Restart Claude Code or reload plugins

## Usage

Run a review on your current changes:
```
/review-checklist
```

The command will:
1. Analyze recent git changes
2. Check against a comprehensive quality checklist
3. Report issues with severity levels
4. Provide specific, actionable fixes

## Example Output

```
### Code Quality Review

#### 1. Security - CRITICAL
Line 45: `app.ts`
- Issue: User input directly inserted into SQL query
- Risk: SQL injection vulnerability
- Fix: Use parameterized queries instead

#### 2. Performance - MAJOR
Line 112: `utils.ts`
- Issue: Nested loop with O(n²) complexity
- Impact: Scales poorly with larger datasets
- Fix: Use Map for O(n) lookup instead
```

## Token Usage

**Estimated:** 400 tokens

The checklist format is designed to be token-efficient:
- Compact bullet-point structure
- Only reports failures, skips passing checks
- Focused on actionable feedback

## Best Practices

- Run before submitting PRs
- Use in combination with automated linting
- Review the checklist categories to understand coverage
- Adjust severity thresholds based on your project

## Limitations

- Does not replace automated testing
- Requires git history to analyze changes
- Best suited for reviewing diffs, not entire codebases
- Manual review still valuable for architecture decisions

## Contributing

Suggestions for additional checklist items? Open an issue or PR!
