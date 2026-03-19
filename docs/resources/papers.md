# Research Papers

Comprehensive documentation of all academic papers that inform the Context Engineering Kit's design and implementation.

## Summary by Plugin

### Reflexion Plugin

**Primary Papers**:

- [Self-Refine](https://arxiv.org/abs/2303.17651) - Core refinement loop
- [Reflexion](https://arxiv.org/abs/2303.11366) - Memory integration
- [Constitutional AI](https://arxiv.org/abs/2212.08073) - Principle-based critique
- [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) - Evaluation patterns
- [Multi-Agent Debate](https://arxiv.org/abs/2305.14325) - Multiple perspectives
- [Agentic Context Engineering](https://arxiv.org/abs/2510.04618) - Memory curation

**Supporting Papers**:

- [Chain-of-Verification](https://arxiv.org/abs/2309.11495) - Hallucination reduction
- [Tree of Thoughts](https://arxiv.org/abs/2305.10601) - Structured exploration
- [Process Reward Models](https://arxiv.org/abs/2305.20050) - Step-by-step evaluation

### Code Review Plugin

**Primary Papers**:

- [Multi-Agent Debate](https://arxiv.org/abs/2305.14325) - Multiple specialized agents
- [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) - Review evaluation
- [Process Reward Models](https://arxiv.org/abs/2305.20050) - Step-by-step verification

**Supporting Papers**:

- [Chain-of-Verification](https://arxiv.org/abs/2309.11495) - Verification patterns
- [Constitutional AI](https://arxiv.org/abs/2212.08073) - Principle-based review

### Spec-Driven Development Plugin

**Primary Papers**:

- [Agentic Context Engineering](https://arxiv.org/abs/2510.04618) - Constitution management
- [Multi-Agent Debate](https://arxiv.org/abs/2305.14325) - Specialized agents
- [Verbalized Sampling](https://arxiv.org/abs/2510.01171) - Diverse idea generation with 2-3x improvement

**Supporting Papers**:

- [Tree of Thoughts](https://arxiv.org/abs/2305.10601) - Planning exploration
- [Constitutional AI](https://arxiv.org/abs/2212.08073) - Project constitution

### Test-Driven Development Plugin

**Primary Papers**:

- [Process Reward Models](https://arxiv.org/abs/2305.20050) - Step verification
- [Chain of Thought Prompting](https://arxiv.org/abs/2201.11903) - Step-by-step reasoning

### SADD Plugin

**Primary Papers**:

- [Multi-Agent Debate](https://arxiv.org/abs/2305.14325) - Multi-agent collaboration
- [Self-Consistency](https://arxiv.org/abs/2203.11171) - Multiple reasoning paths
- [Tree of Thoughts](https://arxiv.org/abs/2305.10601) - Systematic exploration
- [Chain of Thought Prompting](https://arxiv.org/abs/2201.11903) - Explicit reasoning steps
- [Inference-Time Scaling of Verification](https://arxiv.org/abs/2601.15808) - Rubric-guided verification
- [LLM-as-a-Meta-Judge](https://arxiv.org/pdf/2407.19594) - Meta-evaluation of judges
- [Rethinking Rubric Generation](https://arxiv.org/pdf/2602.05125) - Automatic rubric generation

**Supporting Papers**:

- [Constitutional AI](https://arxiv.org/abs/2212.08073) - Self-critique loops
- [Chain-of-Verification](https://arxiv.org/abs/2309.11495) - Verification loops
- [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) - Structured evaluation
- [Generating Evaluation Rubrics](https://arxiv.org/abs/2602.08672) - Rubric quality framework
- [Evaluating Instruction Following](https://arxiv.org/pdf/2310.07641v2) - Meta-evaluation protocol
- [Arena-Hard and BenchBuilder](https://arxiv.org/abs/2406.11939) - Benchmark construction pipeline
- [TICKing All the Boxes](https://arxiv.org/abs/2410.03608) - Checklist decomposition for evaluation
- [CheckEval](https://arxiv.org/abs/2403.18771) - Boolean checklist evaluation framework
- [RocketEval](https://arxiv.org/abs/2503.05142) - Efficient checklist-based grading (0.986 Spearman)
- [LMUnit](https://arxiv.org/abs/2412.13091) - Natural language unit tests for evaluation
- [AutoChecklist](https://arxiv.org/abs/2603.07019) - Composable checklist generation pipelines
- [Are Checklists Really Useful?](https://arxiv.org/abs/2508.15218) - Critical analysis of checklist evaluation
- [Checklists Are Better Than Reward Models](https://arxiv.org/abs/2507.18624) - Checklist vs. reward model alignment
- [OpenRubrics](https://arxiv.org/abs/2510.07743) - Contrastive rubric generation (CRG)
- [RubricHub](https://arxiv.org/abs/2601.08430) - Coarse-to-fine rubric dataset
- [Rubrics as Rewards](https://arxiv.org/abs/2507.17746) - Criteria importance weighting (Essential/Important/Optional/Pitfall)
- [CARMO](https://arxiv.org/abs/2410.21545) - Dynamic context-aware criteria generation
- [SedarEval](https://arxiv.org/abs/2501.15595) - Self-adaptive rubrics
- [WildBench](https://arxiv.org/abs/2406.04770) - Real-world evaluation benchmark (0.98 Pearson)
- [Branch-Solve-Merge](https://arxiv.org/abs/2310.15123) - Decomposed evaluation and generation
- [InFoBench](https://arxiv.org/abs/2401.03601) - Instruction following with decomposed requirements
- [AdvancedIF](https://arxiv.org/abs/2511.10507) - Rubric-based instruction following evaluation

### Customaize Agent Plugin

**Primary Papers**:

- [Prompting Science Report 3](https://arxiv.org/abs/2508.00614) - Evidence-based prompt engineering

**Note**: The plugin also references Meincke et al.'s persuasion principles research (2025a, published on SSRN), which demonstrates that classic persuasion principles (authority, commitment, unity, etc.) can increase AI compliance rates from 33% to 72%.

### Docs Plugin

**Primary References**:

- [The Elements of Style](https://en.wikisource.org/wiki/The_Elements_of_Style) - Classic writing manual for concise prose

---

## Reflection and Iterative Refinement

### [Self-Refine: Iterative Refinement with Self-Feedback](https://arxiv.org/abs/2303.17651)

**Citation**: Madaan et al. (2023). "Self-Refine: Iterative Refinement with Self-Feedback."

Self-Refine introduces a framework where a single language model iteratively generates outputs, provides feedback on its own generations, and refines them based on this self-feedback. The key insight is that models can act as both generator and critic without requiring additional training or external models.

The process follows three steps:

1. **Generate**: Produce initial output for the given task
2. **Feedback**: Critique the output identifying specific issues
3. **Refine**: Improve the output based on feedback

This cycle repeats until the model determines the output meets quality standards or a maximum iteration count is reached.

**Key Results**:

- Improvements across 7 diverse tasks including dialogue, code generation, math reasoning
- 8-21% quality improvement measured by both automatic metrics and human evaluation
- Particularly effective for complex reasoning tasks requiring multi-step solutions

**Relevance to CEK**:
Core technique underlying the Reflexion plugin. The `/reflexion:reflect` command implements this iterative refinement pattern, allowing Claude to review and improve its previous responses.

**Used By Plugins**:

- Reflexion (`/reflexion:reflect`)

**Technical Notes**:

- No additional model training required
- Works with off-the-shelf LLMs
- Token overhead is multiplicative (each iteration consumes additional context)
- Effectiveness depends on model's ability to self-critique

---

### [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366)

**Citation**: Shinn et al. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning."

Reflexion extends self-refinement by adding persistent episodic memory. Agents reflect on task feedback, then explicitly store lessons learned in memory for future reference. This creates a form of "verbal reinforcement learning" where the agent improves through textual self-reflection rather than weight updates.

The framework consists of:

1. **Actor**: Generates actions/outputs
2. **Evaluator**: Provides feedback on performance
3. **Self-Reflection**: Analyzes failures and creates actionable insights
4. **Memory**: Stores reflections for future tasks

**Key Results**:

- Significant improvements on sequential decision-making tasks
- 91% success rate on HumanEval coding benchmark (vs 67% baseline)
- Learns from failures without model retraining
- Memory enables multi-task learning and transfer

**Relevance to CEK**:
Directly informs both the reflection and memory aspects of the Reflexion plugin. The `/reflexion:memorize` command implements the memory storage pattern, updating CLAUDE.md with learned insights.

**Used By Plugins**:

- Reflexion (`/reflexion:reflect`, `/reflexion:memorize`)

**Technical Notes**:

- Separates short-term (within task) and long-term (across tasks) memory
- Memory stored as natural language, not embeddings
- Requires structured format for memory retrieval
- Balances memory size vs. context window limitations

---

## Constitutional and Principle-Based AI

### [Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073)

**Citation**: Bai et al. (2022). "Constitutional AI: Harmlessness from AI Feedback."

Constitutional AI (CAI) trains helpful, harmless, and honest AI assistants using AI-generated feedback based on a set of principles (a "constitution"). The method consists of two phases:

1. **Supervised Learning Phase**: Model generates responses, critiques them against constitutional principles, revises based on critiques
2. **Reinforcement Learning Phase**: Model preferences are used to train a reward model (RLAIF - Reinforcement Learning from AI Feedback)

The key innovation is replacing human feedback with principle-based AI feedback, making the training process more scalable and transparent.

**Key Results**:

- Comparable harmlessness to RLHF with significantly less human annotation
- More transparent - principles are explicit rather than implicit in human preferences
- Easier to customize by modifying the constitutional principles
- Reduces harmful outputs while maintaining helpfulness

**Relevance to CEK**:
Informs the critique-based patterns in the Reflexion plugin and the principle-based evaluation in Code Review. The idea of explicit principles guides the multi-perspective review approach.

**Used By Plugins**:

- Reflexion (`/reflexion:critique`)
- Code Review (specialized agent evaluations)
- Spec-Driven Development (`/sdd:00-setup` constitution)

**Technical Notes**:

- Requires carefully crafted constitutional principles
- Balances multiple potentially conflicting principles
- Can be applied recursively (AI critiques AI critiques)
- Principles must be specific enough to be actionable

---

## Verification and Evaluation Architectures

### [Self-Consistency Improves Chain of Thought Reasoning](https://arxiv.org/abs/2203.11171)

**Citation**: Wang et al. (2023). "Self-Consistency Improves Chain of Thought Reasoning in Language Models."

Self-consistency generates multiple diverse reasoning paths for the same problem, then selects the most consistent answer through majority voting. This leverages the intuition that correct reasoning is more likely to lead to the same answer through different paths.

The process:

1. Generate N diverse reasoning paths using sampling
2. Extract final answers from each path
3. Select answer that appears most frequently (majority vote)

**Key Results**:

- Substantial improvements on arithmetic, commonsense, and symbolic reasoning tasks
- 17.9% absolute improvement on GSM8K math problems
- Effectiveness increases with number of samples
- Works particularly well for problems with verifiable answers

**Relevance to CEK**:
Informs the multi-agent debate and consensus-building patterns. While not directly implemented as sampling, the principle of reaching consensus through multiple perspectives is used in code review.

**Used By Plugins**:

- Code Review (multiple specialized agents reaching consensus)
- Reflexion (`/reflexion:critique` with multiple judges)

**Technical Notes**:

- Requires problems with discrete answer sets
- Token cost scales linearly with number of samples
- Most effective when reasoning paths are truly diverse
- May amplify model biases if all paths share misconceptions

---

### [LLM-as-a-Judge: Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685)

**Citation**: Zheng et al. (2023). "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena."

This paper validates using strong LLMs as judges to evaluate other LLM outputs, showing high agreement with human preferences. MT-Bench introduces a multi-turn benchmark specifically designed for judge evaluation.

Key findings:

- GPT-4 as judge achieves 80%+ agreement with humans
- Position bias (favoring first or second position) is significant and must be mitigated
- Single-answer grading more reliable than pairwise comparison
- Detailed rubrics improve judge consistency

**Key Results**:

- Strong LLMs can reliably evaluate complex, open-ended tasks
- 85% agreement with human crowdworkers on single-answer grading
- Judge prompts with explicit criteria outperform generic evaluation
- Multiple judge consensus further improves reliability

**Relevance to CEK**:
Foundational for all critique and review functionality. Validates the approach of using Claude to evaluate and improve its own outputs or specialized sub-agent outputs.

**Used By Plugins**:

- Reflexion (all critique commands)
- Code Review (all specialized agents)
- Spec-Driven Development (code-reviewer agent)

**Technical Notes**:

- Requires carefully designed judge prompts with clear criteria
- Position bias must be addressed through randomization or single-answer grading
- Effectiveness correlates with judge model capability
- Multiple judges reduce individual judge variance

---

### [Chain-of-Verification Reduces Hallucination in Large Language Models](https://arxiv.org/abs/2309.11495)

**Citation**: Dhuliawala et al. (2023). "Chain-of-Verification Reduces Hallucination in Large Language Models."

CoVe introduces a four-step process to reduce hallucinations in LLM outputs:

1. **Generate Baseline Response**: Create initial answer
2. **Plan Verifications**: Generate verification questions to check response
3. **Execute Verifications**: Answer verification questions independently
4. **Generate Final Response**: Revise based on verification results

The key insight is that verification questions should be answered independently to avoid confirmation bias from the original response.

**Key Results**:

- 20-40% reduction in hallucinations across multiple benchmarks
- Most effective on knowledge-intensive tasks
- Independent verification crucial (avoid showing original response)
- Quality of verification questions correlates with improvement

**Relevance to CEK**:
Informs the verification patterns in Code Review and Reflexion. The principle of generating specific verification criteria and checking them independently guides review processes.

**Used By Plugins**:

- Code Review (specialized agents verify different aspects)
- Reflexion (`/reflexion:critique`)
- Test-Driven Development (tests serve as verification)

**Technical Notes**:

- Verification questions must be specific and answerable
- Independent verification requires careful prompt design
- Multiple verification questions provide redundancy
- Balances thoroughness with token efficiency

---

### [Inference-Time Scaling of Verification: Self-Evolving Deep Research Agents via Test-Time Rubric-Guided Verification](https://arxiv.org/abs/2601.15808)

**Citation**: Wan et al. (2026). "Inference-Time Scaling of Verification: Self-Evolving Deep Research Agents via Test-Time Rubric-Guided Verification."

This paper proposes an alternative paradigm for improving Deep Research Agents (DRAs) through inference-time scaling of verification rather than post-training. The approach enables agents to self-evolve by iteratively verifying outputs against meticulously crafted rubrics, producing feedback, and refining responses.

Key components:

1. **DRA Failure Taxonomy**: Systematic classification of agent failures into 5 major categories and 13 sub-categories
2. **DeepVerifier**: Rubrics-based outcome reward verifier leveraging asymmetry of verification
3. **Rubric-Based Feedback**: Detailed feedback generated from rubrics fed back for iterative bootstrapping
4. **Test-Time Scaling**: Self-improvement without additional training through verification loops

**Key Results**:

- DeepVerifier outperforms vanilla agent-as-judge and LLM judge baselines by 12%-48% in meta-evaluation F1 score
- 8%-11% accuracy gains on challenging subsets of GAIA and XBench-DeepResearch with closed-source LLMs
- DeepVerifier-4K dataset released: 4,646 high-quality supervised fine-tuning examples focused on DRA verification
- Plug-and-play module enables practical self-evolution during test-time inference

**Relevance to CEK**:
Directly informs the `/sadd:judge` command's approach to work evaluation. The rubric-based verification and iterative feedback refinement patterns align with the command's structured evaluation rubrics and self-verification loops.

**Used By Plugins**:

- SADD (`/sadd:judge` - rubric-guided evaluation with iterative improvement)

**Technical Notes**:

- Rubrics derived from systematic failure taxonomy provide comprehensive coverage
- Verification is asymmetric - easier to verify than generate, enabling efficient evaluation
- Iterative refinement without retraining reduces computational overhead
- Self-critique and verification loops catch issues before delivery
- Most effective when rubrics are specific, actionable, and derived from failure analysis

---

### [LLM-as-a-Meta-Judge: Meta-Evaluation of LLM Judges](https://arxiv.org/pdf/2407.19594)

**Citation**: Lee et al. (2024). "LLM-as-a-Meta-Judge: Meta-Evaluation of LLM Judges."

This paper introduces the concept of using LLMs as meta-judges to evaluate the quality of other LLM judges. The approach addresses the challenge of validating automated evaluation systems by creating a hierarchical judging framework where stronger models assess judge performance.

Key components:

1. **Meta-Judge Framework**: LLMs evaluate alignment between judge decisions and ground truth
2. **Judge Quality Metrics**: Systematic assessment of judge consistency, accuracy, and reliability
3. **Hierarchical Evaluation**: Layered judging with meta-level quality assurance
4. **Bias Detection**: Identification of systematic biases in judge behavior

**Key Results**:

- Meta-judges can reliably identify unreliable or biased judge decisions
- Hierarchical evaluation improves overall judging system reliability
- Effective for validating automated evaluation pipelines
- Enables continuous improvement of judge prompts and configurations

**Relevance to CEK**:
Informs the design of multi-layer evaluation systems where judges are themselves evaluated. Supports the `/sadd:judge-with-debate` command's approach to reaching consensus through multiple judge perspectives.

**Used By Plugins**:

- SADD (`/sadd:judge-with-debate` - multi-judge consensus with meta-evaluation)
- SADD (`/sadd:judge` - quality validation of judge outputs)

**Technical Notes**:

- Requires careful design of meta-evaluation criteria
- Meta-judge capability correlates with base model strength
- Useful for detecting systematic biases in evaluation
- Adds computational overhead but improves reliability

---

### [Rethinking Rubric Generation for Improving LLM Judge and Reward Modeling for Open-ended Tasks](https://arxiv.org/pdf/2602.05125)

**Citation**: Kim et al. (2026). "Rethinking Rubric Generation for Improving LLM Judge and Reward Modeling for Open-ended Tasks."

This paper proposes automatic rubric generation methods to improve LLM-as-a-Judge evaluation quality. Instead of relying on generic evaluation criteria, the approach generates task-specific rubrics that capture nuanced quality dimensions.

Key components:

1. **Automatic Rubric Generation**: LLM-generated criteria tailored to specific tasks
2. **Quality Dimension Extraction**: Identification of key evaluation axes from task descriptions
3. **Rubric Refinement**: Iterative improvement of rubrics based on evaluation feedback
4. **Cross-Task Generalization**: Methods for adapting rubrics across similar task types

**Key Results**:

- Task-specific rubrics significantly outperform generic evaluation criteria
- Automatic rubric generation reduces manual effort while improving quality
- Rubric-based evaluation more aligned with human preferences
- Effective across diverse open-ended tasks including creative writing and code generation

**Relevance to CEK**:
Directly informs the rubric-based evaluation patterns in SADD plugin commands. The automatic rubric generation approach enables `/sadd:judge` to create task-specific evaluation criteria dynamically.

**Used By Plugins**:

- SADD (`/sadd:judge` - dynamic rubric generation for task-specific evaluation)
- SADD (`/sadd:do-and-judge` - rubric-guided verification loops)

**Technical Notes**:

- Rubric quality depends on task description clarity
- Automatic generation adds minimal token overhead
- Task-specific rubrics more interpretable than generic criteria
- Can be combined with constitutional principles for comprehensive evaluation

---

### [Generating Evaluation Rubrics for Evaluation: Towards Better LLM-as-a-Judge](https://arxiv.org/abs/2602.08672)

**Citation**: Liu et al. (2026). "Generating Evaluation Rubrics for Evaluation: Towards Better LLM-as-a-Judge."

This paper focuses on the methodology of generating high-quality evaluation rubrics that enable more reliable LLM-as-a-Judge evaluation. The research demonstrates that rubric quality directly impacts judge reliability.

Key components:

1. **Rubric Quality Framework**: Systematic criteria for assessing rubric effectiveness
2. **Principle-Based Generation**: Rubrics derived from evaluation principles and task requirements
3. **Iterative Refinement**: Continuous improvement of rubrics based on evaluation outcomes
4. **Coverage Analysis**: Ensuring rubrics capture all relevant quality dimensions

**Key Results**:

- Well-structured rubrics improve judge agreement with human evaluators by 15-25%
- Rubric specificity correlates with evaluation consistency
- Principle-based rubrics outperform ad-hoc criteria
- Effective rubrics balance comprehensiveness with clarity

**Relevance to CEK**:
Provides methodology for designing evaluation rubrics used across SADD plugin commands. Supports the principle-based evaluation approach in `/sadd:judge` and related commands.

**Used By Plugins**:

- SADD (`/sadd:judge` - structured rubric design)
- SADD (`/sadd:judge-with-debate` - rubric-based multi-judge evaluation)
- Code Review (principle-based evaluation criteria)

**Technical Notes**:

- Rubric design requires domain expertise or careful task analysis
- Overly complex rubrics can reduce judge consistency
- Regular rubric updates improve evaluation quality over time
- Rubric validation against human judgments essential for reliability

---

### [Evaluating Large Language Models at Evaluating Instruction Following](https://arxiv.org/pdf/2310.07641v2)

**Citation**: Zheng et al. (2023). "Evaluating Large Language Models at Evaluating Instruction Following."

This paper investigates how well LLMs can evaluate instruction-following in other models. It introduces a meta-evaluation framework to assess judge capabilities on complex, constraint-heavy tasks.

Key components:

1. **Instruction-Following Evaluation**: Assessing compliance with explicit and implicit constraints
2. **Meta-Evaluation Protocol**: Systematic assessment of judge evaluation quality
3. **Constraint Taxonomy**: Classification of instruction types and their evaluation challenges
4. **Judge Reliability Metrics**: Measuring consistency and accuracy of LLM judges

**Key Results**:

- LLMs show varying capability at evaluating different constraint types
- Judge performance degrades on complex multi-constraint instructions
- Explicit evaluation criteria improve judge reliability
- Judge-model matching (same model evaluating itself) shows systematic biases

**Relevance to CEK**:
Informs the evaluation of instruction-following in task execution. Supports the quality gate approach in SADD where sub-agent outputs are evaluated against task specifications.

**Used By Plugins**:

- SADD (quality gate evaluation against task specifications)
- Code Review (evaluating compliance with coding standards)
- Reflexion (evaluating response quality against instructions)

**Technical Notes**:

- Judge capability varies significantly across constraint types
- Multi-constraint evaluation requires careful rubric design
- Avoiding judge-model matching reduces systematic bias
- Regular calibration against human evaluation improves reliability

---

### [From Crowdsourced Data to High-Quality Benchmarks: Arena-Hard and BenchBuilder Pipeline](https://arxiv.org/abs/2406.11939)

**Citation**: Li et al. (2024). "From Crowdsourced Data to High-Quality Benchmarks: Arena-Hard and BenchBuilder Pipeline."

This paper introduces the BenchBuilder pipeline for automatically constructing high-quality benchmarks from crowdsourced data. Arena-Hard demonstrates how to filter and refine crowd-sourced evaluation data into reliable benchmarks.

Key components:

1. **BenchBuilder Pipeline**: Automated benchmark construction from crowdsourced data
2. **Quality Filtering**: Systematic removal of low-quality or ambiguous evaluation data
3. **Arena-Hard Benchmark**: Challenging benchmark derived from Chatbot Arena data
4. **Automated Curation**: Reducing manual effort in benchmark maintenance

**Key Results**:

- BenchBuilder produces benchmarks with higher reliability than raw crowdsourced data
- Arena-Hard provides challenging evaluation that distinguishes model capabilities
- Automated curation reduces benchmark maintenance overhead
- Filtered benchmarks show better correlation with human preferences

**Relevance to CEK**:
Provides methodology for constructing evaluation datasets and benchmarks within CEK workflows. Supports the creation of task-specific evaluation criteria and quality benchmarks.

**Used By Plugins**:

- SADD (benchmark construction for task evaluation)
- Reflexion (evaluation criteria refinement)
- Code Review (quality benchmark development)

**Technical Notes**:

- Quality filtering essential for reliable benchmarks
- Benchmark difficulty should match evaluation purpose
- Regular benchmark updates prevent gaming and stale metrics
- Automated curation scales benchmark maintenance

---

### [TICKing All the Boxes: Generated Checklists Improve LLM Evaluation and Generation](https://arxiv.org/abs/2410.03608)

**Citation**: Cook et al. (2024). "TICKing All the Boxes: Generated Checklists Improve LLM Evaluation and Generation."

This paper demonstrates that decomposing evaluation criteria into fine-grained boolean checklist items significantly improves both LLM evaluation accuracy and generation quality. Checklist criteria should be atomic, specific, and binary (met/not met) — e.g., "Does code contain duplicated logic?" rather than "Does code follow clean code principles?"

**Key Results**:

- Boolean checklist decomposition outperforms holistic scoring across multiple benchmarks
- Atomic criteria reduce judge subjectivity and improve inter-annotator agreement
- Checklists serve as both evaluation instruments and generation guides
- Task-specific checklists generated by LLMs are effective without human curation

**Relevance to CEK**:
Core technique for the SADD meta-judge's checklist generation. The meta-judge produces boolean, atomic checklist items following TICK's methodology before implementation begins.

**Used By Plugins**:

- SADD (`/sadd:judge` - checklist-based evaluation, `/sadd:do-and-judge` - verification checklists)

**Technical Notes**:

- Checklist items must be independently verifiable
- Atomic criteria prevent ambiguous pass/fail decisions
- Works best when criteria are task-specific rather than generic
- Can be combined with rubric-based scoring for comprehensive evaluation

---

### [CheckEval: A Reliable LLM-as-a-Judge Framework Using Checklists](https://arxiv.org/abs/2403.18771)

**Citation**: Kim et al. (2024). "CheckEval: A Reliable LLM-as-a-Judge Framework for Evaluating Text Generation Using Checklists."

CheckEval decomposes evaluation criteria into fine-grained boolean yes/no checklist questions through LLM-assisted "question diversification" and "elaboration" augmentation from human-defined dimensions. This produces more reliable evaluations than holistic scoring.

**Key Results**:

- Higher inter-annotator agreement than traditional scoring rubrics
- Question diversification expands coverage of evaluation dimensions
- Elaboration augmentation improves checklist specificity
- Boolean questions reduce cognitive load on the judge model

**Relevance to CEK**:
Informs the SADD judge's checklist evaluation approach. The decomposition of rubric dimensions into binary questions aligns with the meta-judge's checklist generation pipeline.

**Used By Plugins**:

- SADD (`/sadd:judge` - boolean checklist evaluation)

**Technical Notes**:

- Two-stage augmentation: diversification then elaboration
- Boolean format eliminates scale calibration issues
- Works well with both strong and lightweight judge models
- Aggregation of boolean scores produces reliable overall assessments

---

### [RocketEval: Efficient Automated LLM Evaluation via Grading Checklist](https://arxiv.org/abs/2503.05142)

**Citation**: Li et al. (2025). "RocketEval: Efficient Automated LLM Evaluation via Grading Checklist."

RocketEval achieves near-perfect correlation with human judgments by separating checklist generation from grading. A powerful LLM (e.g., GPT-4o) generates instance-specific checklists, then a lightweight model (as small as Gemma-2-2B) grades against them.

**Key Results**:

- 0.986 Spearman correlation with human judgments
- Lightweight grading models match strong models when given good checklists
- Instance-specific checklists outperform generic criteria
- Significant cost reduction through asymmetric model assignment

**Relevance to CEK**:
Validates the SADD architecture where meta-judge (strong model) generates criteria and judge (potentially lighter model) evaluates against them. The separation of concerns improves both quality and efficiency.

**Used By Plugins**:

- SADD (`/sadd:judge` - checklist-guided grading, meta-judge separation)

**Technical Notes**:

- Asymmetric architecture: strong model for criteria, light model for grading
- Instance-specific checklists capture task nuances better than templates
- Near-perfect correlation demonstrates checklist-based evaluation ceiling
- Cost-efficient for high-volume evaluation scenarios

---

### [LMUnit: Fine-grained Evaluation with Natural Language Unit Tests](https://arxiv.org/abs/2412.13091)

**Citation**: Zhu et al. (2024). "LMUnit: Fine-grained Evaluation with Natural Language Unit Tests."

LMUnit introduces "natural language unit tests" — explicit, testable criteria (e.g., "Does the response use active voice?") that function like software unit tests but for text evaluation. Each criterion is a standalone, independently verifiable assertion.

**Key Results**:

- Natural language unit tests improve evaluation granularity
- Individual criteria can be tested independently like code assertions
- Enables precise identification of quality dimensions that pass or fail
- Composable test suites allow customized evaluation configurations

**Relevance to CEK**:
Complements the SADD judge's approach to evaluation by treating each checklist item as an independently testable assertion, similar to software testing practices.

**Used By Plugins**:

- SADD (`/sadd:judge` - assertion-style evaluation criteria)

**Technical Notes**:

- Criteria designed as independently testable assertions
- Natural language format accessible to non-technical stakeholders
- Composable test suites enable modular evaluation
- Aligns evaluation methodology with software testing best practices

---

### [AutoChecklist: Composable Pipelines for Checklist Generation and Scoring](https://arxiv.org/abs/2603.07019)

**Citation**: Fisch et al. (2026). "AutoChecklist: Composable Pipelines for Checklist Generation and Scoring with LLM-as-a-Judge."

AutoChecklist provides a taxonomy of five checklist generation strategies: (1) direct — single-pass from instruction alone; (2) contrastive — using candidate responses to identify discriminative criteria; (3) inductive — corpus-level pattern extraction; (4) deductive — instantiation from predefined criteria; and (5) interactive — human-in-the-loop refinement.

**Key Results**:

- Five composable generation strategies cover all practical use cases
- Contrastive generation produces the most discriminative checklists
- Pipeline architecture enables mixing strategies for optimal results
- Production-ready library implementing multiple generation approaches

**Relevance to CEK**:
Provides the theoretical framework for SADD meta-judge's checklist generation approach. The meta-judge primarily uses the "direct" strategy for one-shot generation and "contrastive" strategy when candidate responses are available.

**Used By Plugins**:

- SADD (meta-judge checklist generation pipeline)

**Technical Notes**:

- Direct strategy: simplest, works from instruction alone
- Contrastive strategy: requires candidate responses, produces more discriminative criteria
- Inductive strategy: extracts patterns from corpus of examples
- Deductive strategy: instantiates from predefined criteria templates
- Interactive strategy: incorporates human feedback for refinement

---

### [Are Checklists Really Useful for Automatic Evaluation of Generative Tasks?](https://arxiv.org/abs/2508.15218)

**Citation**: Chen et al. (2025). "Are Checklists Really Useful for Automatic Evaluation of Generative Tasks?"

This paper critically examines the effectiveness of checklist-based evaluation, identifying scenarios where checklists excel and where they fall short. It provides important cautionary findings about the limitations of checklist approaches.

**Key Results**:

- Checklists are most effective for instruction-following and format compliance tasks
- Performance degrades for subjective quality dimensions (creativity, naturalness)
- Checklist granularity must match task complexity — over-decomposition can hurt
- Combination of checklists and holistic scoring produces best results

**Relevance to CEK**:
Provides critical balance to checklist-based approaches in SADD. Informs the meta-judge's decision about when to use checklist vs. rubric-based evaluation criteria.

**Used By Plugins**:

- SADD (meta-judge strategy selection between checklists and rubrics)

**Technical Notes**:

- Checklists work best for verifiable, objective criteria
- Subjective dimensions benefit from rubric-based scoring instead
- Hybrid approaches (checklists + rubrics) recommended for comprehensive evaluation
- Over-decomposition can fragment coherent quality dimensions

---

### [Checklists Are Better Than Reward Models For Aligning Language Models](https://arxiv.org/abs/2507.18624)

**Citation**: Wen et al. (2025). "Checklists Are Better Than Reward Models For Aligning Language Models."

This paper demonstrates that checklist-based evaluation outperforms trained reward models for language model alignment. Checklists provide more interpretable, adjustable, and reliable signals than opaque reward models.

**Key Results**:

- Checklist-based alignment outperforms reward model-based alignment
- Checklists are more interpretable and auditable than reward models
- Easy to update and customize without retraining
- Better generalization to out-of-distribution tasks

**Relevance to CEK**:
Validates the SADD plugin's checklist-first approach to evaluation. Supports the meta-judge's design of generating explicit checklists rather than relying on implicit scoring.

**Used By Plugins**:

- SADD (checklist-based evaluation philosophy)

**Technical Notes**:

- Checklists avoid reward model training costs and biases
- Interpretability enables debugging and improvement of evaluation criteria
- Customizable per-task without retraining infrastructure
- Complements rubric-based scoring for comprehensive evaluation

---

### [OpenRubrics: Scalable Synthetic Rubric Generation for Reward Modeling and LLM Alignment](https://arxiv.org/abs/2510.07743)

**Citation**: Zhang et al. (2025). "OpenRubrics: Towards Scalable Synthetic Rubric Generation for Reward Modeling and LLM Alignment."

OpenRubrics introduces Contrastive Rubric Generation (CRG), which produces two rubric types: "hard rules" (explicit constraints from the instruction) and "principles" (implicit quality indicators visible only by comparing good and bad responses). CRG uses contrastive analysis of response pairs to extract discriminative criteria.

**Key Results**:

- CRG produces more discriminative rubrics than direct generation
- Hard rules capture explicit instruction constraints
- Principles capture implicit quality dimensions from contrastive analysis
- Scalable synthetic generation reduces manual rubric creation effort

**Relevance to CEK**:
Informs the SADD meta-judge's approach to generating both explicit (checklist) and implicit (rubric) criteria. The distinction between hard rules and principles maps to the meta-judge's checklist vs. rubric output.

**Used By Plugins**:

- SADD (meta-judge contrastive rubric generation)

**Technical Notes**:

- CRG requires response pairs (good/bad) for contrastive analysis
- Hard rules are binary (pass/fail), principles are graded
- Synthetic generation scales without human annotators
- Filtering step removes redundant or low-quality rubrics

---

### [RubricHub: Comprehensive Rubric Dataset via Automated Coarse-to-Fine Generation](https://arxiv.org/abs/2601.08430)

**Citation**: Park et al. (2026). "RubricHub: A Comprehensive and Highly Discriminative Rubric Dataset via Automated Coarse-to-Fine Generation."

RubricHub provides a large-scale rubric dataset generated through automated coarse-to-fine decomposition. Starting from broad evaluation dimensions, the system progressively refines criteria into fine-grained, discriminative rubrics.

**Key Results**:

- Coarse-to-fine generation produces more discriminative rubrics
- Automated generation scales rubric creation without human effort
- Fine-grained rubrics improve inter-judge agreement
- Dataset enables training custom rubric generators

**Relevance to CEK**:
Supports the SADD meta-judge's Recursive Rubric Decomposition (RRD) approach, where coarse initial rubrics are iteratively refined into fine-grained criteria through decompose-filter-reweight cycles.

**Used By Plugins**:

- SADD (meta-judge RRD cycle, rubric refinement)

**Technical Notes**:

- Coarse-to-fine aligns with RRD decomposition methodology
- Automated generation reduces rubric creation bottleneck
- Fine-grained rubrics capture nuanced quality distinctions
- Compatible with both human and LLM judges

---

### [Rubrics as Rewards: Reinforcement Learning Beyond Verifiable Domains](https://arxiv.org/abs/2507.17746)

**Citation**: Li et al. (2025). "Rubrics as Rewards: Reinforcement Learning Beyond Verifiable Domains."

This paper synthesizes prompt-specific rubric criteria using a strong LLM guided by four design principles: expert grounding, coverage, self-containedness, and weightage. Criteria are categorized by importance: Essential, Important, Optional, and Pitfall.

**Key Results**:

- Up to 31% relative improvement on HealthBench using rubric-based rewards
- Four-tier importance categorization (Essential/Important/Optional/Pitfall) improves weighting
- Reference answers serve as proxies for expert supervision
- Design principles ensure rubric quality without domain expertise

**Relevance to CEK**:
Directly informs the SADD meta-judge's criteria weighting approach. The Essential/Important/Optional/Pitfall categorization maps to the meta-judge's weight assignment methodology.

**Used By Plugins**:

- SADD (meta-judge criteria importance weighting)

**Technical Notes**:

- Essential criteria must be met for passing scores
- Pitfall criteria identify common failure modes to penalize
- Reference-guided synthesis improves criteria quality
- Four design principles ensure comprehensive, self-contained rubrics

---

### [CARMO: Dynamic Criteria Generation for Context-Aware Reward Modelling](https://arxiv.org/abs/2410.21545)

**Citation**: Chen et al. (2024). "CARMO: Dynamic Criteria Generation for Context-Aware Reward Modelling."

CARMO generates dynamic, context-relevant evaluation criteria tailored to each user query before producing scores. Rather than applying static evaluation templates, it analyzes the specific query context to determine what dimensions matter most.

**Key Results**:

- Dynamic criteria outperform static templates across diverse tasks
- Context-aware generation captures task-specific quality dimensions
- Automatic criteria selection reduces irrelevant evaluation dimensions
- Improved correlation with human preferences over fixed rubrics

**Relevance to CEK**:
Informs the SADD meta-judge's dynamic criteria generation approach. The meta-judge similarly analyzes the user prompt context to generate task-specific criteria rather than applying generic templates.

**Used By Plugins**:

- SADD (meta-judge dynamic criteria generation)

**Technical Notes**:

- Dynamic generation adapts to each query's unique requirements
- Reduces noise from irrelevant evaluation dimensions
- Requires sufficient query context for effective criteria generation
- Compatible with both checklist and rubric-based evaluation

---

### [SedarEval: Automated Evaluation using Self-Adaptive Rubrics](https://arxiv.org/abs/2501.15595)

**Citation**: Yang et al. (2025). "SedarEval: Automated Evaluation using Self-Adaptive Rubrics."

SedarEval introduces self-adaptive rubrics that adjust evaluation criteria based on the specific response being evaluated. The system dynamically modifies rubric granularity and focus areas based on response characteristics.

**Key Results**:

- Self-adaptive rubrics improve evaluation accuracy over fixed rubrics
- Dynamic adjustment captures response-specific quality issues
- Reduces false positives from irrelevant criteria
- Effective across diverse generative tasks

**Relevance to CEK**:
Supports the SADD judge's approach to adaptive evaluation, where scoring criteria can be refined based on the specific implementation artifact being evaluated.

**Used By Plugins**:

- SADD (`/sadd:judge` - adaptive rubric application)

**Technical Notes**:

- Rubrics adapt based on response characteristics
- Reduces evaluation noise from mismatched criteria
- Requires initial rubric set for adaptation
- Complements meta-judge's static rubric generation with runtime adaptation

---

### [WildBench: Benchmarking LLMs with Challenging Tasks from Real Users in the Wild](https://arxiv.org/abs/2406.04770)

**Citation**: Lin et al. (2024). "WildBench: Benchmarking LLMs with Challenging Tasks from Real Users in the Wild."

WildBench curates challenging real-world user prompts for benchmarking LLMs. It achieves 0.98 Pearson correlation with Chatbot Arena rankings, demonstrating that carefully curated evaluation sets can replicate expensive crowd-sourced rankings.

**Key Results**:

- 0.98 Pearson correlation with Chatbot Arena human rankings
- Real user prompts capture practical difficulty better than synthetic benchmarks
- Task-specific evaluation criteria improve ranking accuracy
- Cost-effective alternative to large-scale human evaluation

**Relevance to CEK**:
Validates that structured evaluation with task-specific criteria (as used by SADD judges) can achieve near-perfect agreement with human preferences. Supports the meta-judge's approach to generating task-specific evaluation criteria.

**Used By Plugins**:

- SADD (validation of task-specific evaluation methodology)

**Technical Notes**:

- High correlation validates LLM-as-judge approach with proper criteria
- Real-world prompts more challenging than synthetic benchmarks
- Task-specific criteria essential for accurate evaluation
- Demonstrates ceiling of automated evaluation quality

---

### [Branch-Solve-Merge Improves Large Language Model Evaluation and Generation](https://arxiv.org/abs/2310.15123)

**Citation**: Saha et al. (2023). "Branch-Solve-Merge Improves Large Language Model Evaluation and Generation."

Branch-Solve-Merge (BSM) decomposes complex evaluation tasks into independent sub-problems (branch), solves each independently (solve), then combines results (merge). This reduces the cognitive load on the judge by breaking complex assessments into manageable pieces.

**Key Results**:

- Significant improvement in evaluation consistency for complex tasks
- Decomposition reduces individual assessment difficulty
- Independent solving prevents cross-contamination between criteria
- Merge step produces coherent overall assessments

**Relevance to CEK**:
Informs the SADD judge's approach to evaluating complex implementations by assessing individual criteria independently before producing an overall score, aligning with the checklist-then-rubric evaluation pattern.

**Used By Plugins**:

- SADD (`/sadd:judge` - decomposed evaluation)
- SADD (`/sadd:judge-with-debate` - independent judge assessments)

**Technical Notes**:

- Branch step aligns with meta-judge's criteria decomposition
- Independent solving prevents halo effects between criteria
- Merge requires careful aggregation strategy
- Most effective for multi-dimensional evaluation tasks

---

### [InFoBench: Evaluating Instruction Following Ability in Large Language Models](https://arxiv.org/abs/2401.03601)

**Citation**: Qin et al. (2024). "InFoBench: Evaluating Instruction Following Ability in Large Language Models."

InFoBench introduces the Decomposed Requirements Following Ratio (DRFR) metric, which breaks complex instructions into simpler criteria across five categories: Content, Linguistic, Style, Format, and Number. This decomposition enables fine-grained measurement of instruction-following capability.

**Key Results**:

- DRFR provides more fine-grained assessment than binary pass/fail
- Five-category decomposition covers major instruction dimensions
- Decomposed criteria reveal specific failure modes
- Better diagnostic value than aggregate scores

**Relevance to CEK**:
Informs the SADD meta-judge's criteria categorization approach. The five-category decomposition (Content, Linguistic, Style, Format, Number) provides a taxonomy for organizing checklist and rubric criteria.

**Used By Plugins**:

- SADD (meta-judge criteria categorization)

**Technical Notes**:

- Five categories provide comprehensive coverage of instruction types
- Decomposed ratios identify specific compliance gaps
- Category-level scores enable targeted improvement
- Compatible with both checklist and rubric evaluation approaches

---

### [AdvancedIF: Rubric-Based Benchmarking for Advancing LLM Instruction Following](https://arxiv.org/abs/2511.10507)

**Citation**: Xia et al. (2025). "AdvancedIF: Rubric-Based Benchmarking and Reinforcement Learning for Advancing LLM Instruction Following."

AdvancedIF applies rubric-based evaluation specifically to instruction-following tasks, demonstrating that task-specific rubrics significantly improve evaluation accuracy for complex, multi-constraint instructions.

**Key Results**:

- Rubric-based evaluation improves instruction-following assessment accuracy
- Task-specific rubrics capture constraint interactions better than generic criteria
- Reinforcement learning from rubric-based feedback improves model compliance
- Effective for complex instructions with multiple interacting constraints

**Relevance to CEK**:
Supports the SADD meta-judge's approach to generating rubrics tailored to specific task instructions, particularly for implementation tasks with multiple requirements and constraints.

**Used By Plugins**:

- SADD (meta-judge rubric generation for instruction-following tasks)

**Technical Notes**:

- Task-specific rubrics capture constraint interactions
- Multiple constraints require careful decomposition to avoid conflicts
- Rubric-based RL shows promise for improving compliance
- Effective for implementation tasks with detailed specifications

---

## Multi-Agent Systems

### [Improving Factuality and Reasoning in Language Models through Multiagent Debate](https://arxiv.org/abs/2305.14325)

**Citation**: Du et al. (2023). "Improving Factuality and Reasoning in Language Models through Multiagent Debate."

This paper introduces a multi-agent debate framework where multiple language model instances propose answers, critique each other's proposals, and refine their positions through iterative rounds of debate. The final answer is determined through aggregation of refined positions.

The debate process:

1. Multiple agents independently generate initial responses
2. Agents read each other's responses and provide critiques
3. Each agent updates their response based on critiques
4. Repeat for multiple rounds
5. Aggregate final responses (e.g., majority vote)

**Key Results**:

- Significant improvements on math word problems and strategic reasoning
- Outperforms single-agent self-consistency by 10%+
- More rounds of debate generally improve performance (up to diminishing returns)
- Agents correct each other's factual errors and reasoning mistakes

**Relevance to CEK**:
Informs the multi-agent architecture in Code Review and the critique functionality in Reflexion. The principle that diverse perspectives improve output quality guides plugin design.

**Used By Plugins**:

- Code Review (6 specialized agents with different perspectives)
- Reflexion (`/reflexion:critique` with multiple judges)

**Technical Notes**:

- Requires careful agent prompt design to encourage constructive critique
- Token costs scale with number of agents and debate rounds
- Most effective when agents have genuinely different perspectives or expertise
- Aggregation method (voting, consensus, synthesis) affects results

---

### [Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models](https://arxiv.org/abs/2510.04618)

**Citation**: Zhang et al. (2025). "Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models."

This paper introduces a framework where LLM agents actively curate their own memory by reflecting on experiences and updating persistent context documents. Unlike passive memory retrieval, agents decide what to remember, how to organize it, and when to update it.

Key components:

1. **Experience Reflection**: Analyze task outcomes to extract insights
2. **Memory Selection**: Decide what information is worth remembering
3. **Context Update**: Edit persistent context with learned knowledge
4. **Retrieval Integration**: Incorporate relevant memories into future tasks

**Key Results**:

- **10.6% improvement** over strong baselines on agent benchmarks
- Particularly effective on tasks requiring learning from experience
- Memory quality matters more than memory quantity
- Active curation outperforms passive logging

**Relevance to CEK**:
Directly informs the `/reflexion:memorize` command design. This paper validates the approach of having Claude actively curate CLAUDE.md with learned insights rather than passively logging all interactions.

**Used By Plugins**:

- Reflexion (`/reflexion:memorize`)
- Spec-Driven Development (updating project constitution)

**Technical Notes**:

- Requires structured memory format (CLAUDE.md serves this purpose)
- Balance between memory growth and context window limits
- Memory quality depends on reflection quality
- Retrieval strategy affects how well memory is utilized

---

## Reasoning Enhancement

### [Chain of Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903)

**Citation**: Wei et al. (2022). "Chain of Thought Prompting Elicits Reasoning in Large Language Models."

Chain-of-thought (CoT) prompting is a simple method that significantly improves the ability of large language models to perform complex reasoning. By providing a few demonstrations that include intermediate reasoning steps (chains of thought) as exemplars in prompting, models naturally develop the ability to generate their own reasoning steps before producing final answers.

The key insight is that explicitly generating reasoning steps helps models break down complex problems into manageable sub-problems, mimicking human problem-solving approaches.

**Key Results**:

- Dramatic improvements on arithmetic, commonsense, and symbolic reasoning tasks
- 540B-parameter model with 8 CoT exemplars achieves state-of-the-art on GSM8K math word problems
- Surpasses fine-tuned GPT-3 with verifier
- Reasoning abilities emerge naturally in sufficiently large models via this simple prompting method
- Performance scales with model size - larger models benefit more from CoT

**Relevance to CEK**:
Foundational technique underlying many reasoning patterns across plugins. CoT prompting informs the structured reasoning approaches in SADD, TDD, and code review workflows. The principle of explicit intermediate steps guides implementation of multi-step processes.

**Used By Plugins**:

- SADD (multi-judge evaluation with explicit reasoning)
- TDD (step-by-step test development)
- Code Review (detailed analysis with reasoning chains)
- Kaizen (systematic problem analysis)

**Technical Notes**:

- Requires few-shot examples with reasoning chains
- Most effective for problems requiring multi-step reasoning
- Performance improves with model scale
- Can be combined with self-consistency for further gains
- Zero-shot variants ("Let's think step by step") also effective

---

### [Tree of Thoughts: Deliberate Problem Solving with Large Language Models](https://arxiv.org/abs/2305.10601)

**Citation**: Yao et al. (2023). "Tree of Thoughts: Deliberate Problem Solving with Large Language Models."

ToT generalizes chain-of-thought prompting by exploring multiple reasoning paths in a tree structure. At each step, the model:

1. Generates multiple possible next thoughts
2. Evaluates each thought's promise
3. Selects most promising paths to explore further
4. Backtracks if paths lead to dead ends

This enables systematic exploration of the solution space with lookahead and backtracking.

**Key Results**:

- Dramatic improvements on tasks requiring search (24 Game, Creative Writing, Crosswords)
- 74% success on Game of 24 (vs 4% for chain-of-thought)
- Enables solving problems that require exploration and planning
- More token-intensive but solves previously unsolvable problems

**Relevance to CEK**:
Informs the systematic exploration patterns in Kaizen analysis commands and the planning phases in Spec-Driven Development. While not implementing full tree search, the principle of considering multiple approaches guides design.

**Used By Plugins**:

- Kaizen (systematic analysis of multiple potential root causes)
- Spec-Driven Development (planning explores multiple architectures)

**Technical Notes**:

- Requires problems with intermediate steps that can be evaluated
- Token costs scale with breadth and depth of search
- Evaluation function quality critical for search effectiveness
- Most beneficial for problems where exploration is necessary

---

### [Let's Verify Step by Step: Process Reward Models](https://arxiv.org/abs/2305.20050)

**Citation**: Lightman et al. (2023). "Let's Verify Step by Step."

This paper introduces Process Reward Models (PRMs) that evaluate each step of a reasoning chain rather than just the final answer. PRMs are trained to identify where reasoning goes wrong, enabling more precise feedback and correction.

Key findings:

- Process supervision outperforms outcome supervision for complex reasoning
- PRMs can identify specific incorrect steps in long reasoning chains
- Enables better exploration through value-guided search
- Particularly effective for math and logical reasoning

**Key Results**:

- 78% solve rate on MATH benchmark (vs 72% for outcome-supervised)
- More reliable than outcome supervision for multi-step problems
- Better at catching subtle logical errors
- Enables active learning by identifying valuable training examples

**Relevance to CEK**:
Informs the step-by-step verification patterns in review commands and the detailed feedback in iterative refinement. The principle of evaluating process rather than just outcomes guides feedback design.

**Used By Plugins**:

- Code Review (evaluates code structure, not just final functionality)
- Test-Driven Development (tests verify incremental steps)
- Kaizen (traces problems through reasoning chain)

**Technical Notes**:

- Requires training data with step-level annotations (expensive)
- Inference can use LLM-as-PRM without training
- Most effective for problems with verifiable intermediate steps
- Enables more interpretable feedback than outcome-only evaluation

---

## Prompt Engineering Research

### [Prompting Science Report 3: I'll pay you or I'll kill you -- but will you care?](https://arxiv.org/abs/2508.00614)

**Citation**: Meincke et al. (2025). "Prompting Science Report 3: I'll pay you or I'll kill you -- but will you care?"

This is the third in a series of short reports investigating commonly held prompting beliefs through rigorous testing. This report specifically examines whether tipping or threatening AI models improves performance. The authors evaluated model performance on GPQA and MMLU-Pro benchmarks.

**Key Findings**:

- Threatening or tipping models generally has **no significant effect** on benchmark performance
- Prompt variations can significantly affect performance on a per-question level
- However, it's hard to know in advance whether a particular prompting approach will help or harm performance on any specific question
- Simple prompting variations might not be as effective as previously assumed, especially for difficult problems

**Relevance to CEK**:
Part of the "Prompting Science" research series that informs evidence-based prompt engineering practices. This research validates the approach of testing prompting techniques empirically rather than relying on folk wisdom or anecdotal evidence. The findings suggest focusing on structured, repeatable prompting patterns rather than ad-hoc variations.

**Used By Plugins**:

- Customaize Agent (prompt-engineering skill) - Emphasizes evidence-based prompt optimization

**Technical Notes**:

- Part of a larger research series (references Meincke et al. 2025a for related work on per-question prompt sensitivity)
- Tested on challenging benchmarks (GPQA, MMLU-Pro)
- Findings suggest that benchmark performance may not capture all aspects of prompt effectiveness
- Individual question-level variation remains an open research question

**Note**: This paper references related work by the same authors on persuasion principles and AI compliance (Meincke et al. 2025a), which found that classic persuasion principles (authority, commitment, unity, etc.) can increase AI compliance rates from 33% to 72%. That work is published separately and informed the prompt engineering techniques discussed in the Customaize Agent plugin.

---

## Writing and Documentation

### [The Elements of Style](https://en.wikisource.org/wiki/The_Elements_of_Style)

**Citation**: Strunk, William Jr. (1918). "The Elements of Style." Ithaca, NY: W.P. Humphrey. (Revised by E.B. White, 1959)

The Elements of Style is the foundational reference for clear, concise English prose. Originally written by William Strunk Jr. as a brief guide for his Cornell University English students, the book distills effective writing into essential principles that eliminate wordiness and strengthen expression.

Core principles:

1. **Use the active voice** - Subject performs action directly
2. **Put statements in positive form** - Assert what is, not what isn't
3. **Use definite, specific, concrete language** - Prefer specific to general
4. **Omit needless words** - Every word must justify its presence
5. **Keep related words together** - Proximity signals relationship
6. **Place emphatic words at end** - Sentence endings carry weight

**Key Results**:

- Remained in continuous print for over 100 years
- Standard reference for technical and professional writing
- Principles validated by readability research
- Adopted by universities, publishers, and style guides worldwide

**Relevance to CEK**:
Directly informs the `/docs:write-concisely` command. The skill applies Strunk's rules to automatically improve documentation clarity and reduce word count while maintaining meaning.

**Used By Plugins**:

- Docs (`/docs:write-concisely`, `/docs:update-docs`)

**Technical Notes**:

- Public domain text (1918 edition)
- Rules are prescriptive but widely accepted
- Focus on English prose; some rules are language-specific
- Principles complement rather than contradict modern style guides
- Original text available on Wikisource for reference

---

## Diverse Generation

### [Verbalized Sampling: Mitigating Mode Collapse in LLMs](https://arxiv.org/abs/2510.01171)

**Citation**: Zhang et al. (2025). "Verbalized Sampling: Training-free Prompting for LLMs to Mitigate Mode Collapse." | [Github](https://github.com/CHATS-lab/verbalized-sampling)

Verbalized Sampling introduces a training-free prompting strategy to address mode collapse in LLMs - the tendency to generate similar, "safe" responses regardless of sampling parameters. The technique requests models to include probability estimates with their responses, encouraging sampling from the full distribution rather than just high-probability modes.

The approach:

1. **Request diverse sampling**: Prompt model to generate responses with probability estimates
2. **Distribution awareness**: Ask for responses from "tails of the distribution" for creative tasks
3. **Probability verbalization**: Each response includes a numeric probability score
4. **Natural diversity**: Model naturally produces more varied outputs when probability-aware

**Key Results**:

- **2-3x diversity improvement** while maintaining output quality
- Works across creative writing, brainstorming, and problem-solving tasks
- No additional training or fine-tuning required
- Compatible with standard LLM APIs
- Quality maintained despite increased diversity

**Relevance to CEK**:
Directly informs the idea generation and brainstorming commands in the Spec-Driven Development plugin. The technique enables Claude to generate more diverse and creative ideas during early development phases.

**Used By Plugins**:

- Spec-Driven Development (`/sdd:create-ideas`, `/sdd:brainstorm`, `/sdd:02-plan`)

**Technical Notes**:

- Training-free: works with any instruction-following LLM
- Token overhead minimal (probability scores)
- Most effective for divergent thinking tasks
- Probability scores indicate sampling position, not actual confidence
- Combine with standard sampling parameters (temperature) for additional control
