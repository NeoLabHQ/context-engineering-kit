# Reflexion Plugin

Self-refinement framework that introduces feedback and refinement loops to improve output quality through iterative improvement, complexity triage, and verification.

Focused on:

- **Self-refinement** - Agents review and improve their own outputs
- **Multi-agent review** - Specialized agents critique from different perspectives
- **Iterative improvement** - Systematic loops that converge on higher quality
- **Memory integration** - Lessons learned persist across interactions

## Plugin Target

- Decrease hallucinations - reflection usually allows you to get rid of hallucinations by verifying the output
- Make output quality more predictable - same model usually produces more similar output after reflection, rather than after one shot prompt
- Improve output quality - reflection usually allows you to improve the output by identifying areas that were missed or misunderstood in one shot prompt

## Overview

The Reflexion plugin implements multiple scientifically-proven techniques for improving LLM outputs through self-reflection, critique, and memory updates. It enables Claude to evaluate its own work, identify weaknesses, and generate improved versions.

Plugin is based on papers like [Self-Refine](https://arxiv.org/abs/2303.17651) and [Reflexion](https://arxiv.org/abs/2303.11366). These techniques improve the output of large language models by introducing feedback and refinement loops.

They are proven to **increase output quality by 8–21%** based on both automatic metrics and human preferences across seven diverse tasks, including dialogue generation, coding, and mathematical reasoning, when compared to standard one-step model outputs.

On top of that, the plugin is based on the [Agentic Context Engineering](https://arxiv.org/abs/2510.04618) paper that uses memory updates after reflection, and **consistently outperforms strong baselines by 10.6%** on agents.

## Quick Start

```bash
# Install the plugin
/plugin install reflexion@NeoLabHQ/context-engineering-kit

# Use it after completing any task
> claude "implement user authentication"
> /reflexion:reflect

# Save insights to project memory
> /reflexion:memorize
```

[Usage Examples](./usage-examples.md)

## Commands Overview

### /reflexion:reflect - Self-Refinement

Reflect on previous response and output, based on Self-refinement framework for iterative improvement with complexity triage and verification

- Purpose - Review and improve previous response
- Output - Refined output with improvements

```bash
/reflexion:reflect ["focus area or threshold"]
```

#### Arguments

Optional areas to focus or confidence threshold to use, for example "security" or "deep reflect if less than 90% confidence"

#### How It Works

1. **Complexity Triage**: Automatically determines appropriate reflection depth
   - Quick Path (5s): Simple tasks get fast verification
   - Standard Path: Multi-file changes get full reflection
   - Deep Path: Critical systems get comprehensive analysis

2. **Self-Assessment**: Evaluates output against quality criteria
   - Completeness check
   - Quality assessment
   - Correctness verification
   - Fact-checking

3. **Refinement Planning**: If improvements needed, generates specific plan
   - Identifies issues
   - Proposes solutions
   - Prioritizes fixes

4. **Implementation**: Produces refined output addressing identified issues

**Confidence Thresholds**

The command uses confidence levels to determine if further iteration is needed:

- **Quick Path**: No specific threshold (fast verification only)
- **Standard Path**: Requires >70% confidence
- **Deep Reflection**: Requires >90% confidence

If confidence threshold isn't met, the command will iterate automatically.

#### Usage Examples

```bash
# Basic reflection on previous response
> claude "implement user authentication"
> /reflexion:reflect

# Focused reflection on specific aspect
> /reflexion:reflect security

# After complex feature implementation
> claude "add payment processing with Stripe"
> /reflexion:reflect
```

#### Best practices

- Reflect after significant work - Don't reflect on trivial tasks
- Be specific - Provide context about what to focus on
- Iterate when needed - Sometimes multiple reflection cycles are valuable
- Capture learnings - Use `/reflexion:memorize` to preserve insights


### /reflexion:critique - Multi-Perspective Critique

Memorize insights from reflections and updates CLAUDE.md file with this knowledge. Curates insights from reflections and critiques into CLAUDE.md using Agentic Context Engineering

- Purpose - Multi-perspective comprehensive review
- Output - Structured feedback from multiple judges

```bash
/reflexion:critique ["scope or focus area"]
```

#### Arguments

Optional file paths, commits, or context to review (defaults to recent changes)

#### How It Works

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

#### Usage Examples

```bash
# Review recent work from conversation
> /reflexion:critique

# Review specific files
> /reflexion:critique src/auth/*.ts

# Review with security focus
> /reflexion:critique --focus=security

# Review a git commit range
> /reflexion:critique HEAD~3..HEAD
```

#### Best practices

- For important decisions - Use critique for architectural or design choices
- Before major commits - Get multi-perspective review before committing
- Learn from debates - Pay attention to different perspectives in the critique
- Address all concerns - Don't cherry-pick feedback

### /reflexion:memorize - Memory Updates

Comprehensive multi-perspective review using specialized judges with debate and consensus building

- Purpose - Save insights to project memory
- Output - Updated CLAUDE.md with learnings

```bash
/reflexion:memorize ["source or scope"]
```

#### Arguments

Optional source specification (last, selection, chat:<id>) or --dry-run for preview

#### How It Works

1. **Context Harvesting**: Gathers insights from recent work
   - Reflection outputs
   - Critique findings
   - Problem-solving patterns
   - Failed approaches and lessons

2. **Curation Process**: Transforms raw insights into structured knowledge
   - Extracts key insights
   - Categorizes by impact
   - Applies curation rules (relevance, non-redundancy, actionability)
   - Prevents context collapse

3. **CLAUDE.md Updates**: Adds curated insights to appropriate sections
   - Project Context
   - Code Quality Standards
   - Architecture Decisions
   - Testing Strategies
   - Development Guidelines
   - Strategies and Hard Rules

4. **Memory Validation**: Ensures quality of updates
   - Coherence check
   - Actionability test
   - Consolidation review
   - Evidence verification

#### Usage Examples

```bash
# Memorize from most recent work
> /reflexion:reflect
> /reflexion:memorize

# Preview without writing
> /reflexion:memorize --dry-run

# Limit insights
> /reflexion:memorize --max=3

# Target specific section
> /reflexion:memorize --section="Testing Strategies"

# Memorize from critique
> /reflexion:critique
> /reflexion:memorize
```

#### Best practices

- Regular memorization - Periodically save insights to CLAUDE.md
- Review memory - Occasionally review CLAUDE.md to ensure it stays relevant
- Curate carefully - Only memorize significant, reusable insights
- Organize by topic - Keep CLAUDE.md well-structured

## Scientific Foundation

The Reflexion plugin is based on peer-reviewed research demonstrating **8-21% improvement in output quality** across diverse tasks:

### Core Papers

- **[Self-Refine](https://arxiv.org/abs/2305.12966)** - Iterative refinement where the model reviews and improves its own output
- **[Reflexion](https://arxiv.org/abs/2303.11366)** - Self-reflection for autonomous agents with memory
- **[Constitutional AI (CAI)](https://arxiv.org/abs/2212.08073)** - Critique based on principles and guidelines
- **[LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)** - Using LLMs to evaluate other LLM outputs
- **[Multi-Agent Debate](https://arxiv.org/abs/2305.14325)** - Multiple models proposing and critiquing solutions
- **[Agentic Context Engineering](https://arxiv.org/abs/2510.04618)** - Memory updates after reflection (**10.6% improvement**)

### Additional Techniques

- **[Chain-of-Verification (CoVe)](https://arxiv.org/abs/2305.13888)** - Generate, verify, revise cycle
- **[Tree of Thoughts (ToT)](https://arxiv.org/abs/2305.10601)** - Multiple reasoning path exploration
- **[Process Reward Models](https://arxiv.org/abs/2211.07633)** - Step-by-step evaluation

