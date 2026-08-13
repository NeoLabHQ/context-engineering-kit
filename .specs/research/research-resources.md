# Research Resources

Resources that contain research that can be used to build plugins.

## List

[][YOLO Mode (You Only Look Once) automates your entire Phases workflow](https://docs.traycer.ai/tasks/yolo-mode) - Claude have `--dangerously-skip-permissions` flag to skip permissions check, so it can be used to run YOLO Mode without permissions check.
[][Agent0](https://huggingface.co/papers/2511.16043) - Unleashing Self-Evolving Agents from Zero Data via Tool-Integrated Reasoning
- <https://github.com/aiming-lab/Agent0>
[][Solving a Million-Step LLM Task with Zero Errors](https://arxiv.org/abs/2511.09030) - using `cat file | claude -p "query" --output-format` will run Query via SDK, then exit with json output. 
- Adding `--max-turns 3` will limit amount of turns to 3.
- `--json-schema '{"type":"object","properties":{...}}' "query"` will validate the output against a JSON schema.
- `--model` flag to specify the model to use.
- `--permission-mode plan` will run agent in specified permissions mode <https://code.claude.com/docs/en/iam#permission-modes>

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer. Use proactively after code changes.",
    "prompt": "You are a senior code reviewer. Focus on code quality, security, and best practices.",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  },
  "debugger": {
    "description": "Debugging specialist for errors and test failures.",
    "prompt": "You are an expert debugger. Analyze errors, identify root causes, and provide fixes."
  }
}'
```
[][Agent OS](https://buildermethods.com/agent-os) - Agent OS is a spec-driven development system that gives AI agents the structured context they need to write production-quality code.
[x][codemap](https://github.com/JordanCoin/codemap) - map codebase structure
[][Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
[][mgrep](https://github.com/mixedbread-ai/mgrep)
[x][arxhiv MCP](https://hub.docker.com/mcp/server/arxiv-mcp-server/overview)
[][Docker MCP Toolkit](https://docs.docker.com/ai/mcp-catalog-and-toolkit/toolkit/)
[][Arc42 specification template] - Research Arc42 and adapt it for use in Spec Driven Development.
[][Opus soul document](https://gist.github.com/Richard-Weiss/efe157692991535403bd7e7fb20b6695)
[][YAGNI](https://martinfowler.com/bliki/Yagni.html) - Yagni originally is an acronym that stands for “You Aren't Gonna Need It”. It is a mantra from ExtremeProgramming.
[][Extreme Programming](https://martinfowler.com/bliki/ExtremeProgramming.html)
[][Beads task traker cli](https://github.com/steveyegge/beads) - maybe better to create new cli with simplified architecture, that useses only TASKS.md file.
[][Building the 14 Key Pillars of Agentic AI](https://levelup.gitconnected.com/building-the-14-key-pillars-of-agentic-ai-229e50f65986)
[] Three of Thought and etc - Expand papers that used in reflect plugin as separate comamnds/skills/hooks
[][Building Reliable RAG Pipelines Is Still Hard In 2025](https://medium.com/aiguys/building-reliable-rag-pipelines-is-still-hard-in-2025-9ba5fd92601c)
[] LSP server integration with Claude Code
[][Conductor: Google spec driven development kit](https://github.com/gemini-cli-extensions/conductor)
[] Task tracking: https://github.com/hmans/beans https://github.com/rrnewton/minibeads https://github.com/steveyegge/beads
[x][Agent Skills for Context Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)
[][Agent search MCP](https://github.com/exa-labs/exa-mcp-server)
[][First Principles Framework](https://github.com/m0n0x41d/quint-code)
[] Think about way to make reflection work as continues-learning agent. It can trigger on words like "You absolutily right", analyse it and save to CLAUDE.md file correction that user provided.
[][Hookify](https://github.com/anthropics/claude-code/tree/main/plugins/hookify) - advanced hook configuration, that using python skills.
[][Ralph](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum) - continus iteration plugin and orcestrator verision https://github.com/mikeyobrien/ralph-orchestrator
[][Security Reminder](https://github.com/anthropics/claude-code/tree/main/plugins/security-guidance/hooks) - hook that reminds about security best practices.
[] Add git workspaces usage for competitive model writing
[] Research how git notes can be used during code writing and review
[] Research how to add RAG style pipline with vector search to prepent relevant code to context window before code writing
[] Check "Prompting Science" series. https://arxiv.org/abs/2503.04818, https://arxiv.org/abs/2512.05858, https://chatpaper.com/paper/172346, https://arxiv.org/abs/2508.00614, https://www.researchgate.net/publication/392530384_Prompting_Science_Report_2_The_Decreasing_Value_of_Chain_of_Thought_in_Prompting
[] https://arxiv.org/html/2602.16666v1 - Towards a Science of AI Agent Reliability
[] https://arxiv.org/html/2601.06112v1 - ReliabilityBench: Evaluating LLM Agent Reliability Under Production-Like Stress Conditions

## LLM-as-a-Judge Calibration & Rubric Design

Collected while investigating why the strict 1-5 scoring scale in `plugins/sadd/agents/judge.md`, `plugins/sadd/agents/meta-judge.md`, `plugins/sdd/agents/business-analyst.md` and `plugins/sdd/agents/code-reviewer.md` produces 2-3 on acceptable work with newer models, while the pass bar in `plugins/sadd/skills/do-and-judge/SKILL.md` is a hardcoded `4.0`. Problem: absolute Likert scores are not comparable across judge model generations.

### Primary fix — replace Likert bands with binary decomposition

[][CheckEval](https://arxiv.org/abs/2403.18771) (EMNLP 2025) - Attributes low agreement / high variance across evaluator models to subjective criteria + Likert scoring. **+0.45 average inter-model agreement across 12 evaluator models**, reduced variance. Keeps dimensions and strictness; removes only the adjectival bands. Code: <https://github.com/yukyunglee/CheckEval>
  - Pipeline: (1) dimension → human-defined sub-dimensions (their example: Fluency → formatting / grammar / completeness / readability); (2) one Boolean seed question per sub-dimension, then **diversification** (same sub-dimension, different angle: "Are all words spelled correctly?" → "Are all sentences complete, with no fragments?") and **elaboration** (narrower: → "Are proper nouns spelled correctly?"), then an LLM filter dropping questions that are misaligned with quality, inconsistent with the dimension definition, or redundant; (3) score = **proportion of YES** (15/20 = 0.75).
  - Their own readability question — "Is the summary easy to read, without unnecessary complexity?" — is still fuzzy. The agreement gain comes from collapsing the answer space to two options and forcing per-property judgments, NOT from each question being crisp. For code we can do better by anchoring each question to an observable referent (the neighbouring module's idiom, a stated requirement, an existing convention) rather than to an adjective.
[][Rubrics as Rewards (RaR)](https://arxiv.org/abs/2507.17746) - Checklist-style rubrics as reward signal beat direct Likert rewards by up to 28-31% relative. Independent replication of the checklist > Likert effect.
[][OpenRubrics](https://arxiv.org/abs/2510.07743) - **Contrastive Rubric Generation (CRG)**: condition the rubric generator on a preference triplet (prompt `x`, preferred `y+`, rejected `y-`) and ask it to produce criteria explaining why `y+` beats `y-`. A criterion both responses satisfy explains nothing, so it never gets generated — this prevents at generation time the "satisfied by most reasonable implementations" breadth that `meta-judge.md` Stage 6 currently repairs after the fact. Hard rules come from the prompt's explicit requirements, principles from what makes `y+` qualitatively better — same split as `meta-judge.md` Stages 3/4.
  - **Steal this: rubric validation by rejection sampling.** After generating, re-judge both responses with the new rubric; if it fails to rank `y+` above `y-`, discard the rubric. A spec that can't separate known-good from known-bad is broken, and this catches it before it gates real work.
  - Where pairs exist in our pipeline: `do-competitively` / `tree-of-thoughts` (winner vs losers), `do-and-judge` retry loop (iteration N vs rejected N-1). With a single artifact, mutate it deliberately (delete a test, drop a requirement) and require the spec to score the mutant lower.

### Calibration without an upfront golden set

[][Who Drifted: the System or the Judge?](https://arxiv.org/pdf/2606.15474) - Anytime-valid sequential testing attributes score drift to judge vs. system **without a pre-labeled golden set**, using the judge's own historical baseline. Basis for passively accumulating a per-`model_id` profile from runs already performed (e.g. from `.specs/scratchpad/`), instead of shipping a model→profile map in advance.
[][Analyzing Uncertainty of LLM-as-a-Judge: Interval Evaluations with Conformal Prediction](https://arxiv.org/abs/2509.18658) (EMNLP 2025) - Prediction intervals for judge scores from a single evaluation run, with an **ordinal boundary adjustment for discrete rating tasks** (built for 1-5 Likert).
[][SCOPE: Selective Conformal Optimized Pairwise LLM Judging](https://arxiv.org/pdf/2602.13110) - Calibrates an acceptance threshold so error among non-abstained judgments is ≤ user-specified α. Judge abstains instead of rejecting when evidence is weak — principled trigger for escalation / adversarial review.
[][Diagnosing LLM Judge Reliability: Conformal Prediction Sets and Transitivity Violations](https://arxiv.org/html/2604.15302v1) - Split conformal prediction sets over 1-5 Likert scores with coverage guarantees + transitivity analysis for detecting judge inconsistency.

### Offline / one-time calibration authoring

[][AutoCalibrate — Calibrating LLM-Based Evaluator](https://arxiv.org/abs/2309.13308) (LREC 2024) - Infers scoring criteria from a small human-labeled golden set `D*`. Runtime artifact is **static prompt text** — cost is one-time authoring, not per-evaluation.
  - **Drafting**: draw a few-shot subset from `D*` (they swept 4/6/8/10/12 exemplars for summarization, 6-16 for hallucination) into a prompt saying "here are examples with their human scores; infer the criteria that produce them". Repeat **4 Monte-Carlo trials x 3 temperature samples (T=1.0)** ≈ 12 candidate criteria sets. **What is resampled is the exemplar subset and its ordering, not the criteria** — this defeats *label bias* (a subset of mostly high scores teaches that high scores are normal → lenient criteria) and *position bias* (the first exemplar disproportionately shapes the inferred rule). Criteria that survive many draws don't depend on which draw you got.
  - **Revisiting**: run the evaluator with each candidate over `D*`, correlate with human labels, keep top-K (`C ← argTopK_{c∈C} f(c, D*)`).
  - **Refinement**: collect each candidate's mis-scored examples as `D^R`, feed back, ask for edits (modification / paraphrase / adding aspects / recalibration).
  - Caveat: retrieved text does not say the sampling is stratified across score levels. Stratify anyway, per the full-continuum anchor finding above.
[][LLM-Rubric](https://arxiv.org/pdf/2501.00274) (ACL 2024) - Per-dimension question distributions + small calibration network with **judge-specific parameters** mapping to human ratings; 2× RMSE improvement over uncalibrated. Architectural lesson: judge emits raw signal, a separate per-judge mapping owns the decision.
[][Anchor is the key: automated essay scoring with LLMs through prompting](https://www.sciencedirect.com/science/article/pii/S1075293526000413) - An "anchor" is a complete example artifact plus the score it should receive, placed as static text in the judge prompt next to the rubric, before the item under evaluation (single call, zero extra invocations; rubric states the criteria, anchor demonstrates them applied). Providing anchors significantly improves LLM-human agreement, approaching human-human reliability. **Anchors spanning the FULL scoring continuum align better than anchoring only a subset of score points.** Open-access preprint: <https://osf.io/preprints/edarxiv/cbhgz_v1> (ScienceDirect version is paywalled/403). Caveat for our use: anchors calibrate the scale but must match the artifact type, while `meta-judge` generates a fresh task-specific rubric per run — needs per-artifact-type anchor sets (code / docs / config / agent definition).
[][The Impact of Example Selection in Few-Shot Prompting on Automated Essay Scoring Using GPT Models](https://arxiv.org/pdf/2411.18924) - Companion on how to choose the exemplars. Not yet read (PDF extraction failed).

### Score compression / granularity

[][Improving LLM-as-a-Judge Inference with the Judgment Distribution](https://arxiv.org/pdf/2503.03064) - **NOT APPLICABLE to our pipeline — kept for the diagnosis only.** Method: read the softmax over the score tokens (`P("1")..P("5")`) instead of the emitted digit; mean `Σ s·P(s)` instead of argmax. **Mean beats mode in 42/48 settings.** Explains our clustering: the argmax is a step function, so two artifacts of different quality both emit `2`. Also finds **CoT sharpens/collapses the distribution** — removing CoT gave +6.5% for mean vs +1.4% for mode (RewardBench pointwise) — and our `judge.md` mandates CoT-before-score at `:16`, `:243-256`, `:1051`. Blocker: **requires logit access; the paper explicitly excludes Claude.** Takeaway: checklist aggregates (15/20 = 0.75, 21 distinct values) recover the granularity that the mean would give, over a text-only API.
[][G-Eval](https://arxiv.org/abs/2303.16634) - Original probability-weighted scoring: token-level probabilities produce continuous scores because LLMs otherwise emit only a few dominant integers regardless of instructions. Same logprob requirement — same blocker.

### Meta-evaluation — validating a judge change

[][Reliability without Validity](https://arxiv.org/abs/2606.19544) - 21 judges, 9 providers, ~541k judgments. Exact-match agreement systematically overstates judge ability (**kappa deflation 33-41pp** on MT-Bench); judge rankings shift up to 14 positions across benchmarks; high test-retest reliability coexists with severe position bias. Proposes a Minimum Viable Validation Protocol. Validate scoring changes with chance-corrected agreement on hand-labeled artifacts, not with "scores look more reasonable".
[][Who Validates the Validators?](https://arxiv.org/abs/2404.12272) (UIST 2024) - EvalGen; identifies **criteria drift**: users need criteria to grade outputs, but grading outputs is what defines the criteria. Challenges any design assuming rubric generation can be fully independent of observing outputs — relevant to `meta-judge` producing the spec before implementation exists.
[][LLMs-as-Judges: A Comprehensive Survey on LLM-based Evaluation Methods](https://arxiv.org/pdf/2412.05579) - Survey; background reading.
