# Kaizen Plugin

Continuous improvement framework inspired by the Toyota Production System that brings Lean manufacturing principles to software development through systematic problem analysis, root cause investigation, and iterative improvement cycles.

## Plugin Target

- Find root causes - Stop fixing symptoms; address fundamental issues
- Prevent recurrence - Understand why problems exist to prevent similar issues
- Continuous improvement - Small, incremental changes that compound into major gains
- Reduce waste - Identify and eliminate non-value-adding activities in code and processes

## Overview

The Kaizen plugin implements proven manufacturing problem-solving techniques adapted for software development. Named after the Japanese word for "continuous improvement," Kaizen philosophy emphasizes that small, ongoing positive changes can lead to major improvements over time.

The plugin is based on methodologies from the **Toyota Production System (TPS)** and **Lean manufacturing**, which have been validated across industries for over 70 years.

They are based on the idea that most bugs and quality issues are symptoms of deeper systemic problems. Fixing only the symptom leads to recurring issues; finding and addressing the root cause prevents entire classes of problems.

## Quick Start

```bash
# Install the plugin
/plugin install kaizen@NeoLabHQ/context-engineering-kit

# Investigate a bug's root cause
> /why "API returns 500 error on checkout"

# Analyze code for improvement opportunities
> /analyse src/checkout/

# Document a complex problem comprehensively
> /analyse-problem "Database connection exhaustion during peak traffic"
```

[Usage Examples](./usage-examples.md)

## Commands

- [/why](./why.md) - Five Whys Root Cause Analysis. Iterative questioning technique that drills from surface symptoms to fundamental root causes by repeatedly asking "why."
- [/root-cause-tracing](./root-cause-tracing.md) - Bug Tracing Through Call Stack. Systematically traces bugs backward through the call stack to identify where invalid data or incorrect behavior originates.
- [/cause-and-effect](./cause-and-effect.md) - Fishbone Analysis. Systematic exploration of problem causes across six categories using the Ishikawa (Fishbone) diagram approach.
- [/analyse-problem](./analyse-problem.md) - A3 Problem Analysis. Comprehensive one-page problem documentation using the A3 format, covering Background, Current Condition, Goal, Root Cause, Countermeasures, Implementation Plan, and Follow-up.
- [/analyse](./analyse.md) - Smart Analysis Method Selection. Intelligently selects and applies the most appropriate Kaizen analysis technique based on what you're analyzing: Gemba Walk, Value Stream Mapping, or Muda (Waste) Analysis.
- [/plan-do-check-act](./plan-do-check-act.md) - PDCA Improvement Cycle. Four-phase iterative cycle for continuous improvement through systematic experimentation: Plan, Do, Check, Act.


## Skills

- [kaizen](./kaizen.md) - Continuous Improvement Skill. Automatically applied skill guiding continuous improvement mindset, error-proofing, standardized work, and just-in-time principles.

### The Four Pillars of Kaizen

The Kaizen plugin also includes a skill that applies continuous improvement principles automatically during development:

1. Continuous Improvement - Small, frequent improvements compound into major gains. Always leave code better than you found it.
2. Poka-Yoke (Error Proofing) - Design systems that prevent errors at compile/design time, not runtime. Make invalid states unrepresentable.
3. Standardized Work - Follow established patterns. Document what works. Make good practices easy to follow.
4. Just-In-Time (JIT) - Build what's needed now. No "just in case" features. Avoid premature optimization.

---

## Theoretical Foundation

The Kaizen plugin is based on methodologies with over 70 years of real-world validation in manufacturing, now adapted for software development:

### Toyota Production System (TPS)

The foundation of Lean manufacturing, developed at Toyota starting in the 1940s:

- **[The Toyota Way](https://en.wikipedia.org/wiki/The_Toyota_Way)** - 14 principles of continuous improvement and respect for people
- **[Toyota Kata](https://en.wikipedia.org/wiki/Toyota_Kata)** - Scientific thinking routines for improvement (PDCA)
- **Proven Results**: Toyota achieved highest quality ratings while reducing production costs by 50%+

### Lean Manufacturing Principles

- **[Kaizen](https://en.wikipedia.org/wiki/Kaizen)** - Philosophy of continuous improvement through small, incremental changes
- **[Muda (Waste)](https://en.wikipedia.org/wiki/Muda_(Japanese_term))** - Seven types of waste to eliminate
- **[Value Stream Mapping](https://en.wikipedia.org/wiki/Value-stream_mapping)** - Visualizing process flow to identify improvement opportunities
- **Industry Impact**: Lean principles have spread to healthcare, software, services, achieving **20-50% efficiency improvements**

### Problem-Solving Techniques

- **[Five Whys](https://en.wikipedia.org/wiki/Five_whys)** - Developed by Sakichi Toyoda, founder of Toyota Industries
- **[Ishikawa (Fishbone) Diagram](https://en.wikipedia.org/wiki/Ishikawa_diagram)** - Created by Kaoru Ishikawa for quality management
- **[A3 Problem Solving](https://en.wikipedia.org/wiki/A3_problem_solving)** - Toyota's structured approach to problem documentation
- **[PDCA Cycle](https://en.wikipedia.org/wiki/PDCA)** - Deming cycle for iterative improvement
