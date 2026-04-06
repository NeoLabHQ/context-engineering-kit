# SADD Plugin (Subagent-Driven Development)

Execution framework that dispatches fresh subagents for each task with quality gates between iterations, enabling fast parallel development while maintaining code quality.

Focused on:

- **Fresh context per task** - Each subagent starts clean without context pollution from previous tasks
- **Quality gates** - Code review between tasks catches issues early before they compound
- **Parallel execution** - Independent tasks run concurrently for faster completion
- **Sequential execution** - Dependent tasks execute in order with review checkpoints

## Plugin Target

- Prevent context pollution - Fresh subagents avoid accumulated confusion from long sessions
- Catch issues early - Code review between tasks prevents bugs from compounding
- Faster iteration - Parallel execution of independent tasks saves time
- Maintain quality at scale - Quality gates ensure standards are met on every task

## Overview

The SADD plugin provides skills and commands for executing work through coordinated subagents. Instead of executing all tasks in a single long session where context accumulates and quality degrades, SADD dispatches fresh subagents with quality gates.

**Core capabilities:**

- **Sequential/Parallel Execution** - Execute implementation plans task-by-task with code review gates
- **Competitive Execution** - Generate multiple solutions, evaluate with judges, synthesize best elements
- **Work Evaluation** - Assess completed work using LLM-as-Judge with structured rubrics

This approach solves the "context pollution" problem - when an agent accumulates confusion, outdated assumptions, or implementation drift over long sessions. Each fresh subagent starts clean, implements its specific scope, and reports back for quality validation.

The plugin supports multiple execution strategies based on task characteristics, all with built-in quality gates.

## Quick Start

```bash
# Install the plugin
/plugin install sadd@NeoLabHQ/context-engineering-kit

# Use competitive execution for high-stakes tasks
/do-competitively "Design and implement authentication middleware with JWT support"

```

[Usage Examples](./usage-examples.md)

## New in v2.2 Release

Plugin was significantly improved with new agents based on [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) and [LLM-as-a-Meta-Judge](https://arxiv.org/pdf/2407.19594) papers. Now it work as generalized, simplified and distiled version of [Spec-Driven Development](https://cek.neolab.finance/plugins/sdd) plugin. SADD plugin commands uses `meta-judge` agent in parallel with implementation, in order to generate `in-memory` specification and `judge` agent used to critically evaluate the implementation artifacts based on the specification.

Both judges are general purpose, so they are good as at evaluating code implementation same way as documentation, research and simple questions. As a result you should get high quality results with minimal time spend. But if you want insure aligment of code generation with your overral vision, better to use [Spec-Driven Development](https://cek.neolab.finance/plugins/sdd) plugin.

## Commands Overview

- [launch-sub-agent](./launch-sub-agent.md) - This command launches a focused sub-agent to execute the provided task. Analyze the task to intelligently select the optimal model and agent configuration, then dispatch a sub-agent with Zero-shot Chain-of-Thought reasoning at the beginning and mandatory self-critique verification at the end.
- [/do-and-judge](./do-and-judge.md) - Execute a single task with implementation sub-agent, independent judge verification, and automatic retry loop until passing or max retries exceeded.
- [/do-in-parallel](./do-in-parallel.md) - Execute tasks in parallel across multiple targets with intelligent model selection, independence validation, and quality-focused prompting
- [/do-in-steps](./do-in-steps.md) - Execute complex tasks through sequential sub-agent orchestration with intelligent model selection and LLM-as-a-judge verification.
- [/do-competitively](./do-competitively.md) - Execute tasks through competitive generation, multi-judge evaluation, and evidence-based synthesis to produce superior results.
- [/tree-of-thoughts](./tree-of-thoughts.md) - Execute complex reasoning tasks through systematic exploration of solution space, pruning unpromising branches, expanding viable approaches, and synthesizing the best solution.
- [/judge-with-debate](./judge-with-debate.md) - Evaluate solutions through iterative multi-judge debate where independent judges analyze, challenge each other's assessments, and refine evaluations until reaching consensus or maximum rounds.
- [/judge](./judge.md) - Evaluate completed work using LLM-as-Judge with structured rubrics, context isolation, and evidence-based scoring.

## Skills Overview

- [subagent-driven-development](./subagent-driven-development.md) - Task Execution with Quality Gates. Allow it to dispatch fresh subagent for each task with code review between tasks.
- [multi-agent-patterns](./multi-agent-patterns.md) - Multi-Agent Architecture Patterns. Provide guidence for parallel, sequential and debate execution strategies.

## Agents Overview

- [sadd:meta-judge](./agents/meta-judge.md) - Meta-judge agent for generating evaluation specification YAML.
- [sadd:judge](./agents/judge.md) - Judge agent for evaluating implementation artifact with evaluation specification YAML.

## Theoretical Foundation

The SADD plugin is based on the following foundations:

### Agent Skills for Context Engineering

- [Agent Skills for Context Engineering project](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) by Murat Can Koylan

### Research Papers

**Multi-Agent Patterns:**

- [Multi-Agent Debate](https://arxiv.org/abs/2305.14325) - Du, Y., et al. (2023)
- [Self-Consistency](https://arxiv.org/abs/2203.11171) - Wang, X., et al. (2022)
- [Tree of Thoughts](https://arxiv.org/abs/2305.10601) - Yao, S., et al. (2023)

**Evaluation and Critique:**

- [Constitutional AI](https://arxiv.org/abs/2212.08073) - Bai, Y., et al. (2022). Self-critique loops
- [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) - Zheng, L., et al. (2023). Structured evaluation
- [Chain-of-Verification](https://arxiv.org/abs/2309.11495) - Dhuliawala, S., et al. (2023). Verification loops
- [Inference-Time Scaling of Verification](https://arxiv.org/abs/2601.15808) - Wan, et al. (2026). Rubric-guided verification
- [LLM-as-a-Meta-Judge](https://arxiv.org/pdf/2407.19594) - Lee, et al. (2024). Meta-evaluation of judges
- [Rethinking Rubric Generation](https://arxiv.org/pdf/2602.05125) - Kim, et al. (2026). Automatic rubric generation
- [Generating Evaluation Rubrics](https://arxiv.org/abs/2602.08672) - Liu, et al. (2026). Rubric quality framework
- [Evaluating Instruction Following](https://arxiv.org/pdf/2310.07641v2) - Zheng, et al. (2023). Meta-evaluation protocol
- [Arena-Hard and BenchBuilder](https://arxiv.org/abs/2406.11939) - Li, et al. (2024). Benchmark construction pipeline
- [Branch-Solve-Merge](https://arxiv.org/abs/2310.15123) - Saha, et al. (2023). Decomposed evaluation and generation

**Checklist-Based Evaluation:**

- [TICKing All the Boxes](https://arxiv.org/abs/2410.03608) - Cook, et al. (2024). Boolean checklist decomposition
- [CheckEval](https://arxiv.org/abs/2403.18771) - Kim, et al. (2024). Reliable checklist-based LLM-as-Judge
- [RocketEval](https://arxiv.org/abs/2503.05142) - Li, et al. (2025). Efficient checklist grading (0.986 Spearman)
- [LMUnit](https://arxiv.org/abs/2412.13091) - Zhu, et al. (2024). Natural language unit tests
- [AutoChecklist](https://arxiv.org/abs/2603.07019) - Fisch, et al. (2026). Composable checklist generation pipelines
- [Checklists Are Better Than Reward Models](https://arxiv.org/abs/2507.18624) - Wen, et al. (2025). Checklist vs. reward model alignment
- [Are Checklists Really Useful?](https://arxiv.org/abs/2508.15218) - Chen, et al. (2025). Critical analysis of checklist evaluation

**Rubric Generation and Adaptation:**

- [OpenRubrics](https://arxiv.org/abs/2510.07743) - Zhang, et al. (2025). Contrastive rubric generation (CRG)
- [RubricHub](https://arxiv.org/abs/2601.08430) - Park, et al. (2026). Coarse-to-fine rubric dataset
- [Rubrics as Rewards](https://arxiv.org/abs/2507.17746) - Li, et al. (2025). Criteria importance weighting (Essential/Important/Optional/Pitfall)
- [CARMO](https://arxiv.org/abs/2410.21545) - Chen, et al. (2024). Dynamic context-aware criteria generation
- [SedarEval](https://arxiv.org/abs/2501.15595) - Yang, et al. (2025). Self-adaptive rubrics

**Benchmarking and Instruction Following:**

- [WildBench](https://arxiv.org/abs/2406.04770) - Lin, et al. (2024). Real-world evaluation benchmark (0.98 Pearson)
- [InFoBench](https://arxiv.org/abs/2401.03601) - Qin, et al. (2024). Decomposed instruction following requirements
- [AdvancedIF](https://arxiv.org/abs/2511.10507) - Xia, et al. (2025). Rubric-based instruction following evaluation

### Engineering Methodologies

- **Design Studio Method** - Parallel design exploration with critique and synthesis
- **Spike Solutions** (Extreme Programming) - Time-boxed exploration of multiple approaches
- **Ensemble Methods** (Machine Learning) - Combining multiple models for improved performance
