# Customization

Customization options available for the SDD plugin.

## Token Usage and Efficiency

The main limitation of the SDD plugin is the number of tokens you're willing to spend on each task.

In contrast to other plugins in the context-engineering-kit marketplace, this plugin tries to use as many tokens as possible to get the best results. This approach can consume an entire Claude Code session's token budget on a single task, which is why it has default limits like `target-quality` and `max-iterations` set per command. These are predefined in a way that if a task is well-defined and not too big, in the majority of cases, results will be good enough that you will not need to reiterate on it.

If you want better results or want to finish tasks faster, you can adjust command parameters. For example, adding `--target-quality 4.5 --max-iterations 5` to `/plan` or `/implement` allows the orchestrator agent to iterate more toward "ideal" results. Conversely, setting `--target-quality 3.0 --max-iterations 1` makes agents finish when results minimally meet the criteria, iterating only once to resolve issues. This lets you configure each command to balance quality and speed per task run.

If you just want results as fast as the framework can produce them, use the `--fast` preset in the `/plan` command. It limits the number of steps and decreases both target quality and refinement iterations altogether.

If you know certain steps aren't needed for your task, you can use the `--skip` parameter in the `/plan` command. For example, `--skip research` skips the research phase entirely, and `--skip parallelize` skips task parallelization.

Last but not least, you can ask the orchestrator to use only the `haiku` model for all agents. While this may sound unreliable, the MAKER paper found that parallelizing work across multiple smaller models (3–10 per task) can yield results comparable to larger models. This approach hasn't been tested or officially supported in this plugin yet, but it may still work. You can try combining `haiku` with higher `max-iterations` and `target-quality` values to get faster results with acceptable quality.

## Human-in-the-Loop Verification

The initial version of this plugin was designed to produce the highest possible quality solution that an LLM can generate — in other words, to move real-world LLM performance closer to benchmark results. However, in practice, LLMs tend to drift toward sub-optimal solutions, which is not the desired outcome. The current version filters out all non-working and obviously incorrect solutions. That said, the overall quality still depends on the quality of the specification file and, consequently, on the quality of your review of that specification.

In order to incorporate human feedback into the process, you can use the `--human-in-the-loop` parameter in the `/plan` and `/implement` commands. It will pause the process after each phase and ask you to review the results of the last phase before continuing to the next one.

## Epics, User Stories, and Roadmaps

This plugin follows the KISS principle (Keep It Simple, Stupid) to avoid unnecessary complexity. It doesn't yet support epics and roadmaps, because it's currently difficult to keep the model focused on such long-term activities out of the box. However, you can achieve similar results by using the `/add-task` command with dependencies between tasks. This naturally produces a hierarchical structure of tasks that builds into a roadmap.

On top of that, you can define your own process to organize tasks in whatever way suits you and your team. You can write custom prompts that collect tasks into epics or decompose existing epics into multiple smaller tasks.
