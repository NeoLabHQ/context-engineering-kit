# /critique - Multi-Perspective Critique

Comprehensive multi-perspective review using specialized judges with debate and consensus building

- Purpose - Multi-perspective comprehensive review
- Output - Structured feedback from multiple judges

```bash
/critique ["scope or focus area"]
```

## Arguments

Optional file paths, commits, or context to review (defaults to recent changes)

## How It Works

1. **Context Gathering**: Identifies scope of work to review
2. **Parallel Review**: Spawns three specialized judge agents
   - **Requirements Validator**: Checks alignment with original requirements
   - **Solution Architect**: Evaluates technical approach and design
   - **Code Quality Reviewer**: Assesses implementation quality
3. **Cross-Review & Debate**: Judges review each other's findings and debate disagreements
4. **Consensus Report**: Generates comprehensive report with actionable recommendations

**Judge Scoring**

Each judge provides a score out of 10:

- **9-10**: Exceptional quality, minimal improvements needed
- **7-8**: Good quality, minor improvements suggested
- **5-6**: Acceptable quality, several improvements recommended
- **3-4**: Below standards, significant rework needed
- **1-2**: Major issues, substantial rework required

## Usage Examples

```bash
# Review recent work from conversation
> /critique

# Review specific files
> /critique src/auth/*.ts

# Review with security focus
> /critique --focus=security

# Review a git commit range
> /critique HEAD~3..HEAD
```

## Best practices

- For important decisions - Use critique for architectural or design choices
- Before major commits - Get multi-perspective review before committing
- Learn from debates - Pay attention to different perspectives in the critique
- Address all concerns - Don't cherry-pick feedback
