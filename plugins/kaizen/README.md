# Kaizen Plugin

Continuous improvement through structured problem-solving and quality-focused development practices.

## Overview

Kaizen (改善, "continuous improvement") is a Japanese philosophy emphasizing incremental progress through systematic analysis and error prevention. This plugin brings proven Kaizen techniques to software development.

**Philosophy:** Many small improvements compound into major gains. Prevent errors at design time. Follow what works. Build only what's needed.

## What's Included

### Commands

Structured analysis techniques for problem-solving and process improvement:

- **`/why`** - Five Whys root cause analysis
- **`/cause-and-effect`** - Fishbone diagram for multi-factor analysis
- **`/plan-do-check-act`** - PDCA cycle for iterative improvement
- **`/analyse-problem`** - A3 format for comprehensive problem documentation
- **`/analyse`** - Smart dispatcher (Gemba Walk, Value Stream Mapping, Waste Analysis)

### Skill

- **`kaizen`** - Automatically applied skill guiding continuous improvement mindset, error-proofing, standardized work, and just-in-time principles

## Commands

### `/why` - Five Whys Analysis

Drill from symptoms to root causes by repeatedly asking "why."

**Use for:**
- Bug investigation
- Performance issues
- Process failures
- Incident analysis

**Example:**
```
/why Production deployment takes 2 hours
```

**Output:** Iterative analysis revealing root cause with actionable solutions.

---

### `/cause-and-effect` - Fishbone Analysis

Systematically explore causes across six categories: People, Process, Technology, Environment, Methods, Materials.

**Use for:**
- Complex problems with multiple contributing factors
- Systemic issues
- Cross-functional problems
- When 5 Whys isn't comprehensive enough

**Example:**
```
/cause-and-effect API response latency over 3 seconds
```

**Output:** Categorical breakdown of all contributing factors with prioritized solutions.

---

### `/plan-do-check-act` - PDCA Cycle

Iterative improvement through Plan → Do → Check → Act cycles.

**Use for:**
- Process optimization
- Continuous improvement initiatives
- Experimental changes
- Measuring improvement impact

**Example:**
```
/plan-do-check-act Reduce build time from 45 to 10 minutes
```

**Output:** Structured cycle tracking hypothesis, implementation, measurement, and next steps.

---

### `/analyse-problem` - A3 Problem Solving

Comprehensive one-page analysis: Background, Current Condition, Goal, Root Cause, Countermeasures, Implementation, Follow-up.

**Use for:**
- Major incidents
- Significant improvements
- Problems requiring documentation
- Cross-team coordination

**Example:**
```
/analyse-problem Database connection pool exhaustion causing downtime
```

**Output:** Complete A3 document ready for stakeholder review and implementation tracking.

---

### `/analyse` - Smart Analysis

Intelligently selects best analysis method based on context:

- **Gemba Walk**: Code exploration, actual vs. documented state
- **Value Stream Mapping**: Workflow bottlenecks, process optimization
- **Muda (Waste Analysis)**: Seven types of waste in code

**Use for:**
- When unsure which technique to use
- Comprehensive codebase analysis
- Process inefficiencies
- Technical debt assessment

**Example:**
```
/analyse authentication implementation
/analyse CI/CD pipeline
/analyse codebase for technical debt
```

**Output:** Guided analysis using the most appropriate technique with actionable findings.

## Skill: Kaizen Mindset

Automatically applied skill guiding development with four core principles:

### 1. Continuous Improvement
- Small, frequent improvements over big bang changes
- Iterative refinement: work → clear → efficient
- Always leave code better than you found it
- One improvement at a time

### 2. Poka-Yoke (Error Proofing)
- Make errors impossible through type system
- Validate at boundaries, use safely everywhere
- Invalid states unrepresentable
- Fail fast at startup, not in production

### 3. Standardized Work
- Follow existing codebase patterns
- Document what works (CLAUDE.md, README)
- Consistency over cleverness
- Automate standards (linters, types, tests)

### 4. Just-In-Time (JIT)
- Build what's needed now, not "just in case"
- YAGNI: You Aren't Gonna Need It
- Optimize when measured, not assumed
- Abstract after pattern proven (Rule of Three)

**Automatically guides:**
- Code implementation and refactoring
- Architecture decisions
- Error handling approaches
- Avoiding over-engineering

## Installation

```bash
/plugin install kaizen@NeoLabHQ/context-engineering-kit
```

## Quick Start

### For Problem Analysis

```bash
# Quick root cause analysis
/why Users seeing 500 errors on checkout

# Complex multi-factor problem
/cause-and-effect Test suite is flaky

# Comprehensive incident documentation
/analyse-problem Production outage last night
```

### For Process Improvement

```bash
# Iterative improvement with measurement
/plan-do-check-act Reduce PR review time from 3 days to 1 day

# Analyze workflow bottlenecks
/analyse deployment process

# Find waste in codebase
/analyse codebase for inefficiencies
```

### For Code Exploration

```bash
# Understand actual implementation
/analyse authentication flow

# Compare docs vs. reality
/analyse payment processing implementation
```

## When to Use Which Command

```
Problem Analysis:
├─ Single root cause → /why
├─ Multiple factors → /cause-and-effect
└─ Major incident → /analyse-problem

Process Improvement:
├─ Iterative optimization → /plan-do-check-act
├─ Workflow bottlenecks → /analyse (auto-selects VSM)
└─ Waste identification → /analyse (auto-selects Muda)

Code Understanding:
└─ Implementation analysis → /analyse (auto-selects Gemba)
```

## Command Selection Guide

**Start with `/why` when:**
- Problem seems straightforward
- Need quick root cause
- Time-constrained

**Escalate to `/cause-and-effect` when:**
- Multiple contributing factors
- 5 Whys reveals complexity
- Cross-domain problem

**Use `/plan-do-check-act` when:**
- Making iterative improvements
- Need to measure impact
- Experimenting with solutions

**Use `/analyse-problem` (A3) when:**
- Major incident or problem
- Need formal documentation
- Stakeholder communication required
- Cross-team coordination

**Use `/analyse` when:**
- Unsure which method to use
- Exploring code or process
- Want comprehensive analysis

## Philosophy

Kaizen emphasizes:

**Continuous over perfect:**
- Ship good enough, improve continuously
- Small steps reduce risk
- Feedback loops drive quality

**Prevention over detection:**
- Error-proof designs
- Type safety over runtime checks
- Validate at boundaries

**Standardization over innovation:**
- Follow proven patterns
- Document what works
- Consistency aids comprehension

**Simplicity over cleverness:**
- Build only what's needed
- Delete speculative code
- Optimize when measured

## Best Practices

### For Analysis

1. **Start small**: Begin with `/why`, escalate if needed
2. **Document findings**: Use A3 for important problems
3. **Measure impact**: PDCA for process improvements
4. **Follow through**: Implement recommendations, don't just analyze

### For Development

1. **Iterate**: Work → Clear → Efficient (three passes)
2. **Error-proof**: Use types to prevent errors
3. **Follow patterns**: Check existing code first
4. **Keep it simple**: YAGNI beats speculation

### For Teams

1. **Share learnings**: Document A3s for organizational knowledge
2. **Standardize**: Codify what works in CLAUDE.md
3. **Improve continuously**: Regular retrospectives with PDCA
4. **Build quality in**: Poka-Yoke > post-production fixes

## Examples

### Example 1: Bug Investigation

```bash
# Start with quick analysis
/why Users can't upload files over 5MB

# Root cause found: upload timeout
# Solution: Increase timeout + add progress indicator
```

### Example 2: Performance Optimization

```bash
# Structured improvement cycle
/plan-do-check-act Reduce page load time from 3s to <1s

# Cycle 1: Optimize images (3s → 2s)
# Cycle 2: Add caching (2s → 1.2s)
# Cycle 3: Code splitting (1.2s → 0.8s) ✓
```

### Example 3: Technical Debt

```bash
# Comprehensive codebase analysis
/analyse authentication module

# Gemba Walk reveals:
# - Legacy endpoint unsecured
# - OAuth not implemented (docs say it is)
# - 3 different session mechanisms
# Actions: Security fix + doc update + consolidation plan
```

## Integration with Other Plugins

**Works well with:**

- **TDD**: Kaizen skill guides test-first approach
- **Reflexion**: PDCA cycle for iterative refinement
- **SDD**: A3 format for spec documentation
- **Code Review**: Kaizen mindset for incremental improvements

## Scientific Basis

Kaizen and related techniques proven effective:

- **Toyota Production System**: 50+ years of manufacturing excellence
- **Lean Software Development**: Adapted from TPS principles
- **5 Whys**: Root cause analysis standard across industries
- **PDCA**: Deming cycle, foundation of quality management

## Further Reading

- [Toyota Production System](https://en.wikipedia.org/wiki/Toyota_Production_System)
- [Kaizen Philosophy](https://en.wikipedia.org/wiki/Kaizen)
- [5 Whys Technique](https://en.wikipedia.org/wiki/Five_whys)
- [PDCA Cycle](https://en.wikipedia.org/wiki/PDCA)
- [A3 Problem Solving](https://en.wikipedia.org/wiki/A3_problem_solving)
- [Lean Software Development](https://en.wikipedia.org/wiki/Lean_software_development)

## Support

For issues or suggestions, open an issue in the [Context Engineering Kit repository](https://github.com/NeoLabHQ/context-engineering-kit).

