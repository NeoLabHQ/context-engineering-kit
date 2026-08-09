---
title: Add evaluation benchmarks
---

## Initial User Prompt

add evaluation benchmarks

### Requirements

- Create benchmarks/deep-swe/ folder
- Add there scripts tha capable to run https://deepswe.datacurve.ai/run benchmark
- It should run benchmark with few specifics:
    - Use claude-code, not mini-swe-bench agent.
    - Claude code should have context-engineering-kit/sdd plugin enabled. - this probbaly require extending pier config https://github.com/datacurve-ai/pier for claude code, TODO: research how to do it.
    - tasks should be run as `/do-and-judge --model <model-for-benchmark> <task-as-regular>` - TODO: research how to do it.
- It should provides scripts to do following:
    - run a single task
    - run sample of tasks
    - run full benchmark
- regardless prompt and model, it should support following cases to benchmark:
    - haiku as orcestrator + implementation/judge haiku
    - sonnet as orcestrator + implemenetation/judge haiku
    - sonnet as orcestrator + implementation/judge sonnet
    - haiku as orcestrator + implementation/judge haiku
    - opus as orcestrator + implementation/judge sonnet
    - opus as orcestrator + implementation/judge opus
- It should save results of benchmark in json/csv format.
- Add script that can generate minimal html report from results. It should include vertical bar chart of model group comparision, in each group model itself, compaired agains skill benchmar where it orccestartor and implementation. Plus separatly, vertical bar chart of model group comparision, in each group model itself, compaired agains skill benchmar where orcestrator and implementaion are different, grouped by orcestrator model. Use vercel style for charts.
- Add benchmarks/deep-swe/README.md how to run benchmarks.


## Description

// Will be filled in future stages by business analyst
