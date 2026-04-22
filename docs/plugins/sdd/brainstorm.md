# /brainstorm - Idea Refinement

Transform rough ideas into fully-formed designs through collaborative dialogue, incremental validation, and design documentation.

- Purpose - Refine vague ideas into actionable designs
- Output - Design document in `.specs/plans/<topic>.design.md`

```bash
/brainstorm initial feature concept
```

## Arguments

Optional initial concept to explore. Can be vague: "something to help with user onboarding" or more specific: "real-time notification system".

## How It Works

1. **Context Understanding**:
   - Reviews current project state (files, docs, recent commits)
   - Asks questions one at a time to refine the idea
   - Prefers multiple choice questions when possible
   - Focuses on: purpose, constraints, success criteria

2. **Approach Exploration**:
   - Proposes 2-3 different approaches with trade-offs
   - Leads with recommended option and reasoning
   - Presents options conversationally

3. **Design Presentation**:
   - Breaks design into 200-300 word sections
   - Asks after each section if it looks right
   - Covers: architecture, components, data flow, error handling, testing
   - Ready to clarify if something doesn't make sense

4. **Documentation**:
   - Writes validated design to `.specs/plans/<topic>.design.md`
   - Commits the design document to git

5. **Implementation Handoff** (optional):
   - Asks if ready to set up for implementation
   - Can create isolated workspace with git worktrees
   - Can create detailed implementation plan

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design in sections, validate each

## Usage Examples

```bash
# Start with vague idea
/brainstorm Something to improve user onboarding

# More specific concept
/brainstorm Real-time collaboration features for document editing

# Technical exploration
/brainstorm Caching strategy for our product catalog API

# Process improvement
/brainstorm Automated deployment pipeline for our microservices
```

## Best practices

- Start with the problem - Describe what you're trying to solve
- Be open to alternatives - The first idea isn't always best
- Engage with questions - Your answers shape the design
- Validate incrementally - Catch issues early in design sections
- Save the design - Use as input for `/add-task`
