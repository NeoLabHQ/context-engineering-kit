# Context Engineering Kit

Hand-crafted production ready Claude Code plugin marketplace focused on improving agent result quality.

Contains collection of plugins that allow to use proven techniques and patterns for context engineering with minimal efforts.

## Key Features

- **Simple to Use** - Easy to install and use without any dependencies. Contain automatically used skills and self-explanatory commands.
- **Token-Efficient** - Carefully crafted prompts and architecture, prefering commands over skills, to minimize populating context with unnecessary information.
- **Quality-Focused** - Each plugin focused on meaningfully improving agent result over specific area. Developoed by experienced developers that need to get relaible results on production code.
- **Granular** - Install only the plugins you need. Each plugin loads only its specific agents, commands, and skills.
- **Well-targeted** - Marketplace contains minimal amount of plugins, without overlap and redundant skills. It is based on prompts that used by our company developers daily for long time, with combained plugins from high quality projects. If you looking for more general plugins, take a loog at [Based on section](#based-on)
- **Scientifically proven** - Plugins are based on proven techniques and patterns that were tested by well-trusted benchmarks and studies.

## Quick Start

### Step 1: Add the Marketplace

Add this marketplace to Claude Code:

```bash
# Open Claude Code
claude

# Add the Perplexity marketplace
/plugin marketplace add NeoLabHQ/context-engineering-kit
```

This makes all plugins available for installation, but does not load any agents or tools into your context.

### Step 2: Install Plugins

```bash
# Install any plugins
/plugin install reflexion@NeoLabHQ/context-engineering-kit
```

Each installed plugin loads only its specific agents, commands, and skills into Claude's context.

### Step 3: Use Plugins

```bash
# start claude code
> claude "suggest how to improve codebase"

# Reflect on previus response and improve it if needed
> /reflextion:reflect

# Identify issues and stretegies to solve them, and update CLAUDE.md with this knowledge
> /reflextion:memorize
```

## Full list of Plugins

To view all available plugins:

```bash
/plugin
```

- [Reflexion](#reflexion) - Introduce feedback and refinement loops to improve output quality.
- [Code Review](#code-review) - Introduce codebase and PR review commands and skills using multiple specialized agents.
- [Git](#git) - Introduces commands for commit and PRs creation.
- [Test-Driven Development](#test-driven-development) - Introduces commands for test-driven development, common anti-patterns and skills for testing using subagents.
- [Subagent-Driven Development](#subagent-driven-development) - Introduces skills for subagent-driven development, dispatches fresh subagent for each task with code review between tasks, enabling fast iteration with quality gates.
- [Domain-Driven Development](#domain-driven-development) - Introduces command to update CLAUDE.md with best practices for domain-driven development, focused on quality of code, includes Clean Architecture, SOLID principles, and other design patterns.
- [Spec-Driven Development](#spec-driven-development) - Introduces commands for specification-driven development, based on Github Spec Kit and OpenSpec. Uses specialized agents for effective context management and quality review.
- [Kaizen](#kaizen) - Inspired by Japanese continuous improvement philosophy, Agile and Lead development practices. Introduces commands for analytisis of root cause of issues and problems, including 5 Whys, Cause and Effect Analysis, and other techniques.
- [Customaize Agent](#customaize-agent) - Commands and skills for writing and refining commands, hooks, skills for Claude Code, includes Anthropic Best Practices and [Agent Persuasion Principles](https://arxiv.org/abs/2508.00614) that can be usefull for sub-agent workflows.
- [Docs](#docs) - Commands for analaysing project, writing and refining documentation.
- [Language and Frameworks Best Practices](#language-and-frameworks-best-practices) - Commands for setup or update of CLAUDE.md file with best practices for specific language and frameworks.

### Reflexion

Collection of commands that force LLM to reflect on previus response and output. Based on papers like [Self-Refine](https://arxiv.org/abs/2305.12966) and [Reflexion](https://arxiv.org/abs/2303.11366). This techniques improve the output of large language models by introducing feedback and refinement loops.

```bash
/plugin install reflexion@NeoLabHQ/quality-agent
```

They proven to **increase output quality to 8–21%** based on both automatic metrics and human preferences across seven diverse tasks, including dialogue generation, coding and mathematical reasoning, when compared to standard one-step model outputs.

Full list of included patterns and techniques:

- [Self-Refinement / Iterative Refinement](https://arxiv.org/abs/2303.17651) - One model generates, then reviews and improves its own output
- [Constitutional AI (CAI) / RLAIF](https://arxiv.org/abs/2212.08073) - One model generates responses, another critiques them based on principles
- [Critic-Generator or Verifier-Generator Architecture](https://arxiv.org/abs/2305.12966) - Generator model creates outputs, Critic/verifier model evaluates and provides feedback
- [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) - One LLM evaluates/scores outputs from another LLM
- [Debate / Multi-Agent Debate](https://arxiv.org/abs/2305.14325) - Multiple models propose and critique solutions
- [Generate-Verify-Refine (GVR)](https://arxiv.org/abs/2305.02424) - Three-stage process: generate → verify → refine based on verification

On top of that plugin based on [Agentic Context Engineering](https://arxiv.org/abs/2510.04618) paper that uses memeory updates after reflection, that **consistently outperform strong baselines by 10.6%** on agents.

Also inlcudes following techniques:

- [Chain-of-Verification (CoVe)](https://arxiv.org/abs/2305.13888) - model generates answer, then verification questions, then revises
- [Tree of Thoughts (ToT)](https://arxiv.org/abs/2305.10601) - explores multiple reasoning paths with evaluation
- [Process Reward Models (PRM)](https://arxiv.org/abs/2211.07633) - evaluate reasoning steps rather than just final answers

## Based on <a name="based-on"></a>

This project improves plugins collected across multiple projects and marketplaces.

List of main sources:

- [Official Claude Code plugins](https://github.com/anthropics/claude-code/tree/main/plugins)
- [Claude Task Master](https://github.com/eyaltoledano/claude-task-master)
- [Multi-agent Orchestration](https://github.com/wshobson/agents)
- [Anthropic example skills](https://github.com/anthropics/skills)
- [Claude Flow](https://github.com/ruvnet/claude-flow)
- [Superpowers](https://github.com/obra/superpowers/tree/main)
- [Awesome Claude Skills](https://github.com/ComposioHQ/awesome-claude-skills)
- [Beads](https://github.com/steveyegge/beads)

## Recomendend MCP Servers

Servers recommended for use with this marketplace:

- [Context7](https://github.com/upstash/context7)
- [Serena](https://github.com/oraios/serena)
- [Perplexity Model Context Protocol](https://github.com/perplexityai/modelcontextprotocol)

## Recomended Specification Driven Development Projects

This marketplace incapsualte best from this project, but you may want to use full power of this techniques from following projects:

- [Github Spec Kit](https://github.com/github/spec-kit)
- [OpenSpec](https://github.com/Fission-AI/OpenSpec)
- [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD)
