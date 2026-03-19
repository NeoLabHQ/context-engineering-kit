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
```

```bash
> claude "implement user authentication"
# Claude implements user authentication, then you can ask it to reflect on implementation

> /reflexion:reflect
# It analyses results and suggests improvements
# If issues are obvious, it will fix them immediately
# If they are minor, it will suggest improvements that you can respond to
> fix the issues

# If you would like it to avoid issues that were found during reflection to appear again,
# ask claude to extract resolution strategies and save the insights to project memory
> /reflexion:memorize
```

Alternatively, you can use the `reflect` word in initial prompt:

```bash
> claude "implement user authentication, then reflect"
# Claude implements user authentication,
# then hook automatically runs /reflexion:reflect
```

In order to use this hook, need to have `bun` installed. But for overall command it is not required.

[Usage Examples](./usage-examples.md)

## Automatic Reflection with Hooks

The plugin includes optional hooks that automatically trigger reflection when you include the word "reflect" in your prompt. This removes the need to manually run `/reflexion:reflect` after each task.

### How It Works

1. Include the word "reflect" anywhere in your prompt
2. Claude completes your task
3. The hook automatically triggers `/reflexion:reflect`
4. Claude reviews and improves its work

```bash
# Automatic reflection triggered by "reflect" keyword
> Fix the bug in auth.ts then reflect
# Claude fixes the bug, then automatically reflects on the work

> Implement the feature, reflect on your work
# Same behavior - "reflect" triggers automatic reflection
```

**Important**: Only the exact word "reflect" triggers automatic reflection. Words like "reflection", "reflective", or "reflects" do not trigger it.

## Commands

- [/reflexion:reflect](./reflect.md) - Self-Refinement. Reflect on previous response and output, based on Self-refinement framework for iterative improvement with complexity triage and verification
- [/reflexion:critique](./critique.md) - Multi-Perspective Critique. Memorize insights from reflections and updates CLAUDE.md file with this knowledge. Curates insights from reflections and critiques into CLAUDE.md using Agentic Context Engineering
- [/reflexion:memorize](./memorize.md) - Memorize insights from reflections and updates CLAUDE.md file with this knowledge. Curates insights from reflections and critiques into CLAUDE.md using Agentic Context Engineering

## Theoretical Foundation

Based on papers like [Self-Refine](https://arxiv.org/abs/2303.17651) and [Reflexion](https://arxiv.org/abs/2303.11366). These techniques improve the output of large language models by introducing feedback and refinement loops.

They are proven to **increase output quality by 8–21%** based on both automatic metrics and human preferences across seven diverse tasks, including dialogue generation, coding, and mathematical reasoning, when compared to standard one-step model outputs.

Full list of included patterns and techniques:

- [Self-Refinement / Iterative Refinement](https://arxiv.org/abs/2303.17651) - One model generates, then reviews and improves its own output
- [Constitutional AI (CAI) / RLAIF](https://arxiv.org/abs/2212.08073) - One model generates responses, another critiques them based on principles
- [Critic-Generator or Verifier-Generator Architecture](https://arxiv.org/abs/2510.14660v1) - Generator model creates outputs, Critic/verifier model evaluates and provides feedback
- [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) - One LLM evaluates/scores outputs from another LLM
- [Debate / Multi-Agent Debate](https://arxiv.org/abs/2305.14325) - Multiple models propose and critique solutions
- [Generate-Verify-Refine (GVR)](https://arxiv.org/abs/2204.05511) - Three-stage process: generate → verify → refine based on verification

On top of that, the plugin is based on the [Agentic Context Engineering](https://arxiv.org/abs/2510.04618) paper that uses memory updates after reflection, and **consistently outperforms strong baselines by 10.6%** on agents.

Also includes the following techniques:

- [Chain-of-Verification (CoVe)](https://arxiv.org/abs/2309.11495) - Model generates answer, then verification questions, then revises
- [Tree of Thoughts (ToT)](https://arxiv.org/abs/2305.10601) - Explores multiple reasoning paths with evaluation
- [Process Reward Models (PRM)](https://arxiv.org/abs/2305.20050) - Evaluates reasoning steps rather than just final answers