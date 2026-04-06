

Do following:
- Refine plugins/customaize-agent/skills/create-rule/SKILL.md to properly follow skill structure and have proper rule creation process (follow plugins/customaize-agent/skills/create-skill/SKILL.md).
- Create meta judge agent in the sadd plugin
- Create judge agent in the sadd plugin
- create new set-rule skill in sadd plugin that should add or modify .claude/rules, by using meta judge.

## Description

Check existing plugins/sdd/prompts/judge.md for use it as basis for the meta judge and simple judge.

### Meta Judge

Sources:
 @https://www.themoonlight.io/en/review/learning-to-judge-llms-designing-and-applying-evaluation-rubrics
 @https://github.com/lmarena/arena-hard-auto/blob/196f6b826783b3da7310e361a805fa36f0be83f3/utils/judge_utils.py - Arena Hard judge prompt

Meta Judge should produce checklist,criteria/metrics and weight by folloding GER‑Eval’s methodology based on the user prompt, befoire implementation even starts. This information will be used by the judge to evaluate the implementation artifact.

Role and task declaration: define the meta judge as a strict evaluator, not a helper

He should produce YAML or JSON entries of the form:

- name: short label (“Factual accuracy”),
-description: what the dimension means and what it covers,
- scale: either numeric (1–5) or categorical ({poor, fair, good, excellent, ideal}),
- instruction: instructions to the judge like “Give 1 if any major factual error is present; give 5 if all claims are supported by the provided context.”

Overral Meta Judge flow:
- Meta judge should collect infomration in codebase or related sources based on user prompt, to generate better criteria and weight.

- Meta judge should create or modify existing .claude/rules if it applicable for prompt in order to provide Contrastive Examples for the judge.

Checklist source: https://arxiv.org/abs/2410.03608
Checklist criteria should be boolean, atomic and specific, so it can be met or not met specificaly, for example "Does code follow clean code principles?" is not correct, but "Does code contain duplicated logic?" is correct. It should contain specific criteria that say whether task was completed or not. For example for prompt: "Write smoke tests for the service", checklist should contain criteria like "Does smoke tests exist?", "Do smoke tests were run and passed?", "Do smoke tests cover endpoints?", but it should not contain "Does smoke test cover all critical paths?" - it is too vague and not specific enough, it can be refined as a rubric/metrics.

Metrics: explicitly describe what to check (e.g., relevance, coherence, faithfulness, helpful, relevant, and concise), again as clear, named dimensions. Describe what each metrics is means, for example in case of simple question and criteria description includes "Helpful means the answer correctly responds to the prompt or follows the instructions. Relevant means all parts of the response closely connect or are appropriate to what is being asked. Concise means the response is clear and not verbose or excessive"

Scoring scheme: define what each score means and the conditions for each bin; avoid “1–10 without definitions”.

Meta judge should use Recursive Rubric Decomposition (RRD) from Rethinking Rubric Generation for Improving LLM Judge and Reward Modeling for Open‑ended Tasks: https://arxiv.org/pdf/2602.05125. Meta judge should start from a coarse initial rubric and run a decompose → filter → reweight cycle to get:
- more fine‑grained, discriminative criteria,
- removal of redundant / correlated criteria, and
- better correlation‑aware weighting over dimensions
The goal is specifically to improve LLM judges and reward models: they show large gains in preference‑judgment accuracy on JudgeBench and other benchmarks, and stronger reward signals for RFT when using RRD‑generated rubrics versus baseline rubrics

Add RRD cycle at the end of process, meta judge after producing rubrics should run cycle at least 1 time before returning the final rubrics.

Additional criteria:
- Explicit criteria list: pass criteria as separate, clearly named items with definitions, not buried in prose
- Structured output: force JSON/YAML with fields like criterion_name, score, reason, possibly with a top‑level overall_label
- Note when user prompt has any ambiguity or more than one interpretation, it is more helpful and appropriate to ask for clarifications or more information from the user than providing an criteria/metrics based on assumptions

### Judge

Judge should evaluate the implementation artifact based on the meta judge criteria and weight.

Role and task declaration: define the judge as a strict evaluator, not a helper

He should produce a score and a justification for the score.
He should produce a verification 5 questions about your evaluation.
He should answer verification questions.

Overral judge flow:
- Judge should collect information in codebase or related sources based on user prompt, to generate better criteria and weight
- Judge should provide his version of the result before judging any answers using think tool.
- When evaluating agent result, compare it with his own result.
- judge must identify and correct any mistakes or inaccurate results
- then reate if agent results based on rurics/crtiteria/metrics/checklist. 
- identify any missing important resuls/artifcats/checks that would be beneficial to include in the end result.

Important to properly set scale, default score allways should be 2, anything upper should be justified. 

After verification if judge has found any issues, he must create/modify .claude/rules to provide better contrastive examples for the next time implementation.

Chain‑of‑thought or explanation: judge should produce the reasoning FIRST, then score; this improves stability and debuggability

#### Abstract judge examples

Examples of evaluation criteria per task type. They too abstract, plugins/sdd/prompts/judge.md is done much better, and still should be used as basis, but this variants provide high level structure for different task types:

**Answer Relevance** example

```markdown
You are an expert evaluator tasked with assessing how well an LLM output addresses its input.

## Evaluation Criteria:

1. Analyze the input to understand what is being asked or requested

2. Examine the output to see what information is provided

3. Determine if the output directly addresses the input

4. Check for irrelevant or off-topic information in the output

5. Assess completeness - does the output answer all aspects of the input?

6. Consider conciseness - is the output appropriately focused?

## Evaluation Instructions:

Evaluate how well the output addresses the input by analyzing the relevance of the response content.

Assign a score from 1 to 5 where:

- 5 = Output perfectly addresses the input with all content being relevant

- 4 = Output mostly addresses the input with minor irrelevant details

- 3 = Output partially addresses the input with some irrelevant content

- 2 = Output barely addresses the input, mostly irrelevant

- 1 = Output does not address the input at all
```

**Task Completion** example

```markdown
You are an expert evaluator tasked with assessing task completion in LLM outputs.

## Evaluation Criteria:

1. Identify the specific task requested in the input

2. Determine all requirements and constraints mentioned

3. Check if the output fulfills each requirement

4. Verify the output format matches any specified format

5. Assess completeness - are all parts of the task done?

6. Validate the quality of task execution

## Evaluation Instructions:

Evaluate whether the output successfully completes the requested task.

Assign a score from 1 to 5 where:

- 5 = Task fully completed with all requirements met

- 4 = Task mostly completed with minor omissions

- 3 = Task partially completed with significant gaps

- 2 = Task barely attempted with major failures

- 1 = Task not completed or attempted

```

Prompt Adhesion

```markdown
You are an expert evaluator tasked with assessing prompt adherence in LLM outputs.

## Evaluation Criteria:

1. Extract all specific instructions from the input

2. Identify format requirements (JSON, list, length, etc.)

3. Check style requirements (tone, perspective, formality)

4. Verify constraint compliance (word limits, exclusions, etc.)

5. Assess structural requirements (sections, order, etc.)

6. Validate all instructions are followed

## Evaluation Instructions:

Evaluate how well the output follows all instructions in the input.

Assign a score from 1 to 5 where:

- 5 = All instructions perfectly followed

- 4 = Most instructions followed with minor deviations

- 3 = Some instructions followed, some ignored

- 2 = Few instructions followed

- 1 = Instructions largely ignored

```

### Integration

Need integrate meta judge and judge to sadd plugin skills: do-and-judge, do-in-steps, do-in-parallel, judge-with-debate.

Each of skills should call meta judge with exact user prompt so it produces the criteria and weight and then call judge to evaluate the implementation artifact.

### Rules

Source: @https://arxiv.org/html/2310.07641v2

Rules should be based on LLMBar evaluator paper: explicit high‑level rules like “prioritize correctness over style; do not reward hallucinated detail”, which significantly and consistently improves evaluator accuracy across both natural and adversarial test sets and include bad/good examples for the implementation agent and judge

Create new /set-rule skill in sadd plugin that should add or modify .claude/rules files with the rules: include there guidlines to launch meta judge to do the modification (meta judge should have all guidlines how to properly write the rules)

#### Rules examples

https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices/rules - React Best Practices from Vercel Labs: uses Description, Incorrect, Correct examples template

Claude code guidlines for rules in plguins/customaize-agent/skills/create-rule/SKILL.md

## Sources

All listed sources already loaded into .specs/research/papers/ directory. You must explore this papers, gather information and apply them in order to implement required agents and skills:
- LLM-as-a-Meta-Judge paper @https://arxiv.org/pdf/2407.19594
- Rethinking Rubric Generation for Improving LLM Judge and Reward Modeling for Open-ended Tasks @https://arxiv.org/pdf/2602.05125
- LLM-as-a-Judge: @https://arxiv.org/abs/2306.05685
- Inference-Time Scaling of Verification: Self-Evolving Deep Research Agents via Test-Time Rubric-Guided Verification: @https://arxiv.org/abs/2601.15808
- Generating Evaluation Rubrics for Evaluation: @https://arxiv.org/abs/2602.08672 - 0.514 Spearman correlation
- Evaluating Large Language Models at Evaluating Instruction Following: @https://arxiv.org/pdf/2310.07641v2
- From Crowdsourced Data to High-Quality Benchmarks: Arena-Hard and BenchBuilder Pipeline: https://arxiv.org/abs/2406.11939
- OpenRubrics: Towards Scalable Synthetic Rubric Generation for Reward Modeling and LLM Alignment: https://arxiv.org/abs/2510.07743 - CRG produces two rubric types: "hard rules" (explicit constraints from the instruction) and "principles" (implicit quality indicators visible only by comparing good and bad responses)
- Contrastive Rubric Generation: https://www.emergentmind.com/topics/contrastive-rubric-generation-crg
- SedarEval: Automated Evaluation using Self-Adaptive Rubrics: https://arxiv.org/abs/2501.15595
- TICKing All the Boxes: Generated Checklists Improve LLM Evaluation and Generation: https://arxiv.org/abs/2410.03608
- WildBench: Benchmarking LLMs with Challenging Tasks from Real Users in the Wild: https://arxiv.org/abs/2406.04770 - 0.98 Pearson correlation
- Checklists Are Better Than Reward Models For Aligning Language Models: https://arxiv.org/abs/2507.18624
- CARMO: Dynamic Criteria Generation for Context-Aware Reward Modelling: https://arxiv.org/abs/2410.21545 - generates dynamic, context-relevant evaluation criteria tailored to each user query before producing scores
- AdvancedIF: Rubric-Based Benchmarking and Reinforcement Learning for Advancing LLM Instruction Following: https://arxiv.org/abs/2511.10507
- LLM-As-Judge: 7 Best Practices & Evaluation Templates: https://www.montecarlodata.com/blog-llm-as-judge/
- Branch-Solve-Merge Improves Large Language Model Evaluation and Generation: https://arxiv.org/abs/2310.15123
- InFoBench: Evaluating Instruction Following Ability in Large Language Models: https://arxiv.org/abs/2401.03601 - Decomposed Requirements Following Ratio, metric for evaluating LLM ability to follow instructions, which breaks complex instructions into simpler criteria across five categories: Content, Linguistic, Style, Format, and Number
- RocketEval: Efficient Automated LLM Evaluation via Grading Checklist: https://arxiv.org/abs/2503.05142 - Achieves 0.986 Spearman correlation - A powerful LLM (GPT-4o) generates instance-specific checklists, then a lightweight model (as small as Gemma-2-2B) grades against them
- CheckEval: A reliable LLM-as-a-Judge framework for evaluating text generation using checklists: https://arxiv.org/abs/2403.18771 - decomposes evaluation criteria into fine-grained Boolean yes/no checklist questions through LLM-assisted "question diversification" and "elaboration" augmentation from human-defined dimensions'
- LMUnit: Fine-grained Evaluation with Natural Language Unit Tests: https://arxiv.org/abs/2412.13091 - introduces "natural language unit tests" — explicit, testable criteria (e.g., "Does the response use active voice?")
- RubricHub: A Comprehensive and Highly Discriminative Rubric Dataset via Automated Coarse-to-Fine Generation: https://arxiv.org/abs/2601.08430 - https://github.com/teqkilla/RubricHub
- Rubrics as Rewards: Reinforcement Learning Beyond Verifiable Domains: https://arxiv.org/abs/2507.17746 - synthesizes prompt-specific rubric criteria using a strong LLM guided by four design principles: expert grounding, coverage, self-containedness, and weightage. Reference answers serve as proxies for expert supervision. Criteria are categorized by importance (Essential, Important, Optional, Pitfall). Achieves up to 31% relative improvement on HealthBench
- AutoChecklist: Composable Pipelines for Checklist Generation and Scoring with LLM-as-a-Judge: https://arxiv.org/abs/2603.07019 - provides the most useful taxonomy of checklist generation approaches, defining five abstractions: (1) direct — single-pass generation from instruction alone; (2) contrastive — using candidate responses to identify discriminative criteria; (3) inductive — corpus-level pattern extraction; (4) deductive — instantiation from predefined criteria; and (5) interactive — human-in-the-loop
- Are Checklists Really Useful for Automatic Evaluation of Generative Tasks?: https://arxiv.org/abs/2508.15218

- https://www.emergentmind.com/topics/openrubrics-framework
- https://www.emergentmind.com/topics/contrastive-rubric-generation-crg
- https://www.themoonlight.io/en/review/learning-to-judge-llms-designing-and-applying-evaluation-rubrics
- https://www.emergentmind.com/papers/2602.05125

## Preview Resserch results

What works best for one-shot generation: Instruction-to-checklist decomposition (TICK, RLCF direct method) is the simplest and most reliable pattern. Contrastive generation using preference pairs (OpenRubrics CRG, CARMO) produces more discriminative rubrics but requires candidate responses. arXivEmergent Mind Reference-guided synthesis (RaR) produces rubrics competitive with human-authored ones when reference answers are available.

Where one-shot falls short: RRD's finding that naive rubrics degrade accuracy is the most important cautionary result. GER-Eval shows scoring reliability degrades in knowledge-intensive settings. arXiv Furuhashi et al. show benefits are inconsistent across tasks. The implication is that one-shot rubric generation is reliable for instruction-following and style evaluation but less so for factual or domain-expert evaluation.

The most actionable papers for someone building a one-shot rubric generation pipeline today are: TICK (for the core decomposition method), OpenRubrics (for contrastive generation with filtering), RaR (for reference-guided synthesis principles), RLCF (for the direct extraction method and WildChecklists dataset), and AutoChecklist (for a production-ready library implementing multiple generation strategies). For training custom generators, RIFL and RubricHub provide the strongest foundations.