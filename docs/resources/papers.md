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

**Supporting Papers**:

- [Constitutional AI](https://arxiv.org/abs/2212.08073) - Self-critique loops
- [Chain-of-Verification](https://arxiv.org/abs/2309.11495) - Verification loops
- [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) - Structured evaluation

### Customaize Agent Plugin

**Primary Papers**:

- [Prompting Science Report 3](https://arxiv.org/abs/2508.00614) - Evidence-based prompt engineering

**Note**: The plugin also references Meincke et al.'s persuasion principles research (2025a, published on SSRN), which demonstrates that classic persuasion principles (authority, commitment, unity, etc.) can increase AI compliance rates from 33% to 72%.

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
