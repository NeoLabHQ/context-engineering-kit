# Potential Benchmarks to Include


[] skill-creator plugin - Anthropic ships its own Skills-evaluation tooling. - Will need to write own tasks and ways to measure quality.

## Correctness / issue-resolution benchmarks

[] SWE-bench Pro (Scale AI): 1,865 instances (731 public, 858 held-out, 276 commercial) across 41 repos; contamination-resistant via GPL/private repos; harder (top models ~23% on public, dropping on private). Docker harness on GitHub.

## Contamination-resistant / live benchmarks

[] SWE-bench-Live (Microsoft): auto-updating, adds ~50 verified issues/month; 1,319+ instances, 93+ repos; multi-language and Windows variants. Frozen Lite/Verified splits for fair comparison.
[] SWE-rebench: automated pipeline continuously extracting fresh, decontaminated interactive SWE tasks (NeurIPS 2025).
[] DeepSWE (Datacurve): hand-authored contamination-free (discussed above).

## long-horizon benchmarks

[] SWE-Lancer (OpenAI): 1,400+ real Upwork freelance tasks worth $1M; independent tasks graded by triple-verified end-to-end (browser) tests; also managerial "choose the proposal" tasks. Open Docker image + public "Diamond" split. Maps performance to dollars; frontier models still fail the majority.
[] METR time-horizon suite: measures the length of tasks (in human-expert time) an agent completes at 50%/80% reliability; uses scaffolds including Claude Code. More a capability-trend measure than a plug-in local harness. 
[] Commit0: 54 Python libraries generated from scratch against a spec + unit tests, with interactive static-analysis/test feedback. Greenfield construction; contamination-aware. Current agents pass few full libraries (best ~29% of unit tests on a subset, ~6% on the full set).

## Function-level / classic code generation

[] BigCodeBench: 1,140 function-level tasks, 139 libraries, complex instructions, high branch coverage. Built on EvalPlus; PyPI-installable; Complete and Instruct splits.
[] EvalPlus / HumanEval+ / MBPP+: augmented HumanEval/MBPP with far more tests; cheap, fast, but saturated and contamination-prone. Good smoke tests, not quality measures.
[] LiveCodeBench: rolling competitive-programming problems (LeetCode/AtCoder/Codeforces) post-cutoff for contamination resistance. Measures algorithmic problem-solving, not software quality.
[] Aider polyglot: 225 hard Exercism exercises across C++, Go, Java, JS, Python, Rust; scored inside Aider's real edit loop with a structured diff format and a second attempt after test failure. Strong practical signal for editing reliability across languages, easy to run, but exercise-style not repo-scale.

## Code-QUALITY-focused

[] https://cognition.com/blog/frontier-code  - paid benchmark
[] https://senior-swe-bench.snorkel.ai/ - senior SWE-bench, evaludates quality and teste
[] SlopCodeBench (arXiv 2603.24755, Orlanski et al., Mar 25 2026): the standout for quality. 20 language-agnostic problems, 93 checkpoints, where the agent iteratively extends its own prior code under evolving specs that force architectural decisions. Tracks verbosity (redundant/duplicated code) and structural erosion (complexity concentration). Findings: no agent solves any problem end-to-end — "the highest checkpoint solve rate is 17.2%" (Opus 4.6); quality degrades monotonically — "erosion rises in 80% of trajectories and verbosity in 89.8%"; "agent code is 2.2x more verbose" than maintained human repos (high-complexity functions rise from 4.1 to 37.0, max cyclomatic complexity from 27.1 to 68.2 across a trajectory); and quality-aware prompting cuts initial verbosity/erosion ~30% and raises cost per checkpoint 12.1% but has "little impact on the iterative degradation." Directly measures maintainability under long-horizon feature-building.
[] RACE: multi-dimensional benchmark — Readability, mAintainability, Correctness, Efficiency — with static-analysis metrics (naming, comments, complexity, maintainability index, modularity) and demand-based requirements. Dockerized eval scripts on GitHub. Finds readability is a critical differentiator and that correctness-only benchmarks miss most quality signal.
[] SmellBench / SWE-Refactor (2026): refactoring-quality benchmarks (code smells, Extract-Method-style transformations, repository-level).
[] FeatureBench (2026): 200 end-to-end feature-development tasks + 3,825 executable environments from 24 repos; execution-based; Claude 4.5 Opus (74.4% on SWE-bench) succeeds on only ~11%.

## Roadmap

[] Add DeepSWE as base benchmark. - Include tests for do-and-judge, do-in-steps. For 
    - sonnet as orcestrator + implemenetation/judge haiku
    - sonnet as orcestrator + implementation/judge sonnet
    - haiku as orcestrator + implementation/judge haiku
    - opus as orcestrator + implementation/judge sonnet
    - opus as orcestrator + implementation/judge opus
[] Add SlopCodeBench or FeatureBench as code quality benchmarks - Focus on SDD plugin, with simular to previus benchmar setup
[] Optinal: senior SWE-bench - evaludates quality and teste
[] Optional: RACE - also code quality benchmarks
[] Optional: Commit0 benchmarks - long-horizon task
[] SWE-Lancer Diamond benchmarks - complex tasks, usefull for SADD and SDD.
