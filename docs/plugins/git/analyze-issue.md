# /analyze-issue - Issue Analysis

Analyze a GitHub issue and create a detailed technical specification.

- Purpose - Transform issues into actionable development tasks
- Output - Technical specification with requirements

```bash
/analyze-issue <issue-number>
```

## Arguments

Issue number (e.g., 42) - required.

## How It Works

1. **Issue Fetching**: Retrieves issue details from GitHub
2. **Requirements Extraction**: Identifies user stories and acceptance criteria
3. **Technical Analysis**: Determines APIs, data models, and dependencies
4. **Task Breakdown**: Creates actionable subtasks
5. **Complexity Assessment**: Estimates implementation effort

## Usage Examples

```bash
# Analyze issue before starting work
> /analyze-issue 123

# Use with SDD workflow
> /analyze-issue 123
> /sdd:01-specify

# Plan sprint work
> /load-issues
> /analyze-issue 45
> /analyze-issue 67
```

## Best Practices

- Analyze before coding - Understand requirements first
- Check issue completeness - Request clarification if needed
- Note dependencies - Identify related issues or PRs
- Use for planning - Helps estimate and prioritize work
