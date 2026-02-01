

# Roadmap for V2 release


## Tasks

[] Move all commands to skills format, in order to properly support all installers
[] Add support for vercel skill installer - but left support for installers that exists now
[] Publish skills in vercel marketplace
[] Migrate SDD plugin to v2 version
    [] Fix issues with scratchpad id generation - potentially write script for generation of them
    [] Write a script that create folder setup and adds scratchpad and reports folders to gitignore
    [] potentially add plan-directly command that allow to plan without using subagents - will move to v2.1
    [] Add support for flags of `/implementaion` command that allow to increase and decreate amount of guality, amount of iterations allowed, `--human-in-the-loop` flag to allow to pause for human verification after each step and `--refine` flag that will perform refinement of implementation after human feedback or corrections. Need check whether it have `--continue` flag, it not then add it.
[] Update project readme with new features and changes. Remove majoirty of content and move it to docs/, also verify with another projects on best practices of readme. And update header image to be transparent.

## Draft announce for V2

> SDD plugin was rewritten from sctratch. It now able to achive working code aligned with initial prompt in 100% of cases that was tested on real-life production projects!

## Darft desciption of SDD v2

SDD Plugin: Spec-Driven Development + Continuous Learning + LLM-as-Judge 

This pluging is designed to consistently produce highest possible quality of solution that LLM agent can produce. Esentially it allow to predictably get results that as close as possible to LLMs benchmark that you using.

Main patterns that implemented in this plugin:

- Multi-agent orcestration for context managment 
- Structured reasoning templates, that include: Zero-shot and Few-shot Chain of Thought, Tree of Thoughts, Problem Decomposition and Self-Critique. Each tailored for specific agent and task that they perform.
- Quality gates based on LLM-as-Judge, that are used to evaluate the quality of each planing and implementation step using evidence-based scoring and predefined rubrics.
- Continuous learning agent pattern used in order to build skills that agent will need in order to implement specific task.
- Spec-driven development pattern based on arc42 specification standard adjusted for LLM capabilities and implemented as structured task planing process.


Features and differences from other frameworks, plugins and agentic orcestrators:

- This plugin was able to generate working code aligned with initial prompt in 100% of cases that was tested on real projects. So, if you was able to get use case that it was not able to handle, please report it as an issue. 
- Main limitation of this workflow is amount of tokens that you willing to spend on each task. Plugin tries to use as much tokens as possible in order to get best results. Within reasonable default limitations. In order to overcome this limitation, each command have predefined parameters that you can configure to balance between quality and speed. For example you can use `--fast` in `/plan` command in order to limit amount of steps, decrease target quality and amount of refinement iterations. On the other hand, you can increase expected result if you wiling to spend more tokens, by using commands like `--target-quality 4.5 --max-iterations 5` that will allow agent iterate more in order to get close to "ideal" results.
- This plugin is not "vibe" coding solution. It expect that developer that using it know what he want to produce and have some level of understanding how to reach there. So he can incorporate critical information and valuable feedback into the process. But by default it is designed to work from single prompt till the end of the task and make evidence based decisions. Because developer time is more valuable than model time. So it will allways produce working results, but quality of it will be sub-optimal if no human feedback is provided.
- Need keep in mind that plugin can produce results that better than model can generate theoretically, which mainly depend on amount of time that you willing to spend refining it. Specifically, after generating specification you can correct it or left comments using `//` and then running `/plan --refine` command again. You also can make verifications after each planinig and implementation phase. By majority of known researches human feedback is most effective way to improve results.
- Our tests showed that even if speicifcation that was generated initially wasn't correct due to lack of information or complexity of the task. Agent will be able correct itself till it reaches working solution. But usally it means that it will stop more frequiently. To avoid such cases we strongly advice to decompose task into smaller separate tasks with dependencies and review specification for each of them. On the other hand, you still can use plugin even for complex tasks, without human verification, but you probably will be need to use tools like ralp-loop in order to keep agent working for longer time.
- This plugin follows princeple of KISS (Keep It Simple Stupid). So it not yet support epics and roadmaps, because it currently problematic to keep model focused on such long term activities. But it already possible to reach simular results by using `/add-task` command with specifying dependencies between tasks. This way you can produce naturally hierarchial structure of tasks that builds into roadmap. On top of that you can manage and define own process to organaize tasks that more suitable for you and your team.
- While majority of other frameworks, work best for new projects and greenfield development.This plugin designed to work better the more code you already have and the better structured architecture of your solution. At each planing phase it have **codebase impact analysis** step, that evaluate which exact files cab be affected by your tasks and what patterns better to follow in order to achive desired result.
- Plugin designed to work as "night build" for your development process. You can write prompt and let it work while you sleep, and you can expect it to produce working result when you return. The amount of time it will spend depends on task complexity, for simple tasks it can work for 30 minutes, for complex tasks it can workk few days.


### Quick start

Switch model to `sonnet[1m]` in order to keep model focused for longer time. (Important: it not means that sonnet will be used for work itself. By default `sonnet` will be used as orcestrator in order to launch `opus` agent that will perform actual work.)

```bash
/model sonnet[1m]
```

Create tasks file with initial prompt

```bash
/add-task "Design and implement authentication middleware with JWT support"
# Output:
# Created task file: .specs/tasks/draft/design-implement-authentication-middleware-with-jwt-support.feature.md
# Title: Design and implement authentication middleware with JWT support
# Type: feature
# Depends on: None
```

You can adjust task file to incorrporate additional details and creiterias at this moment. But it is not required.

Run planing process

```bash
/plan 
```

It will perform following refinement process in order to update task file with more detailed specification:
```
// TODO: add mermaid diagram of the process
```

It will output updated task file to `.specs/tasks/todo/design-implement-authentication-middleware-with-jwt-support.feature.md` and create new skills if it is needed. Plus, it will produce scratchpads and verification reports along the way in order to properly thinking and evaluating each step of the process. (you can simply ignore them).

At this moment you can verify specification and adjust, and then run `/plan --refine` command again in order to agent to update rest of the specification if it not aligned with your cahgnes. By default it uses top-to-bottom approach to update specification, which means that all sections below your changes will be rethinked and updated accordingly.

Once you are happy with specification, you can run implementation process

```bash
/implement
```

It will perform following actions:
```
// TODO: add mermaid diagram of the process
```

It will automatically write tests and verify them, verify build and that solution is working as expected.

Once implementation is complete, you can verify it and adjust, and then run `/implement --refine` command again in order to agent to update rest of the implementation if it not aligned with your cahgnes or feedback.

Once it complete, you can use `context-engineering-kit:git` plugin in order to commit changes and create pull request.

```bash
/git:commit
/git:create-pr
```
