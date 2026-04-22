# /analyse - Smart Analysis Method Selection

Intelligently selects and applies the most appropriate Kaizen analysis technique based on what you're analyzing: Gemba Walk, Value Stream Mapping, or Muda (Waste) Analysis.

- Purpose - Auto-select best analysis method for your target
- Output - Detailed analysis using the most appropriate technique

```bash
/analyse ["target description"]
```

## Arguments

Optional target description (e.g., code area, workflow, or inefficiencies to investigate). You can override auto-selection with METHOD variable.

## How It Works

**Method Selection Logic**:

| Method | Use When Analyzing |
|--------|-------------------|
| **Gemba Walk** | Code implementation, gap between docs and reality, unfamiliar codebase areas |
| **Value Stream Mapping** | Workflows, CI/CD pipelines, bottlenecks, handoffs between teams |
| **Muda (Waste)** | Code quality, technical debt, over-engineering, resource utilization |

**Gemba Walk** ("Go and see"):
1. Define scope of code to explore
2. State assumptions about how it works
3. Read actual code and observe reality
4. Document: entry points, data flow, surprises, hidden dependencies
5. Identify gaps between documentation and implementation
6. Recommend: update docs, refactor, or accept as-is

**Value Stream Mapping**:
1. Identify process start and end points
2. Map all steps including wait/handoff time
3. Measure processing time vs. waiting time for each step
4. Calculate efficiency (value-add time / total time)
5. Identify bottlenecks and waste
6. Design future state with optimizations

**Muda (Waste) Analysis** - Seven types of waste in software:
1. **Overproduction**: Features no one uses, premature optimization
2. **Waiting**: Build time, code review delays, blocked dependencies
3. **Transportation**: Unnecessary data transformations, API layers with no value
4. **Over-processing**: Excessive logging, redundant validations
5. **Inventory**: Unmerged branches, half-finished features, untriaged bugs
6. **Motion**: Context switching, manual deployments, repetitive tasks
7. **Defects**: Production bugs, technical debt, flaky tests

## Usage Examples

```bash
# Explore unfamiliar code
> /analyse authentication implementation

# Optimize a workflow
> /analyse deployment pipeline

# Find waste in codebase
> /analyse codebase for inefficiencies
```

## Best Practices

- Start with Gemba Walk when unfamiliar - Understand reality before optimizing
- Use VSM for process improvements - CI/CD, deployment, code review workflows
- Use Muda for efficiency audits - Technical debt, cleanup initiatives
- Combine methods - Gemba Walk can lead to Muda analysis findings
- Document findings - Use /analyse-problem for comprehensive documentation
