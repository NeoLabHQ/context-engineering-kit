---
name: context-engineering
description: Understand the components, mechanics, and constraints of context in agent systems. Use when writing, editing, or optimizing commands, skills, or sub-agents prompts.
---

# Context Engineering Fundamentals

Context is the complete state available to a language model at inference time. It includes everything the model can attend to when generating responses: system instructions, tool definitions, retrieved documents, message history, and tool outputs. Understanding context fundamentals is prerequisite to effective context engineering.

## Core Concepts

Context comprises several distinct components, each with different characteristics and constraints. The attention mechanism creates a finite budget that constrains effective context usage. Progressive disclosure manages this constraint by loading information only as needed. The engineering discipline is curating the smallest high-signal token set that achieves desired outcomes.

## Detailed Topics

### The Anatomy of Context

**System Prompts**
System prompts establish the agent's core identity, constraints, and behavioral guidelines. They are loaded once at session start and typically persist throughout the conversation. System prompts should be extremely clear and use simple, direct language at the right altitude for the agent.

The right altitude balances two failure modes. At one extreme, engineers hardcode complex brittle logic that creates fragility and maintenance burden. At the other extreme, engineers provide vague high-level guidance that fails to give concrete signals for desired outputs or falsely assumes shared context. The optimal altitude strikes a balance: specific enough to guide behavior effectively, yet flexible enough to provide strong heuristics.

Organize prompts into distinct sections using XML tagging or Markdown headers to delineate background information, instructions, tool guidance, and output description. The exact formatting matters less as models become more capable, but structural clarity remains valuable.

**Tool Definitions**
Tool definitions specify the actions an agent can take. Each tool includes a name, description, parameters, and return format. Tool definitions live near the front of context after serialization, typically before or after the system prompt.

Tool descriptions collectively steer agent behavior. Poor descriptions force agents to guess; optimized descriptions include usage context, examples, and defaults. The consolidation principle states that if a human engineer cannot definitively say which tool should be used in a given situation, an agent cannot be expected to do better.

**Retrieved Documents**
Retrieved documents provide domain-specific knowledge, reference materials, or task-relevant information. Agents use retrieval augmented generation to pull relevant documents into context at runtime rather than pre-loading all possible information.

The just-in-time approach maintains lightweight identifiers (file paths, stored queries, web links) and uses these references to load data into context dynamically. This mirrors human cognition: we generally do not memorize entire corpuses of information but rather use external organization and indexing systems to retrieve relevant information on demand.

**Message History**
Message history contains the conversation between the user and agent, including previous queries, responses, and reasoning. For long-running tasks, message history can grow to dominate context usage.

Message history serves as scratchpad memory where agents track progress, maintain task state, and preserve reasoning across turns. Effective management of message history is critical for long-horizon task completion.

**Tool Outputs**
Tool outputs are the results of agent actions: file contents, search results, command execution output, API responses, and similar data. Tool outputs comprise the majority of tokens in typical agent trajectories, with research showing observations (tool outputs) can reach 83.9% of total context usage.

Tool outputs consume context whether they are relevant to current decisions or not. This creates pressure for strategies like observation masking, compaction, and selective tool result retention.

### Context Windows and Attention Mechanics

**The Attention Budget Constraint**
Language models process tokens through attention mechanisms that create pairwise relationships between all tokens in context. For n tokens, this creates n^2 relationships that must be computed and stored. As context length increases, the model's ability to capture these relationships gets stretched thin.

Models develop attention patterns from training data distributions where shorter sequences predominate. This means models have less experience with and fewer specialized parameters for context-wide dependencies. The result is an "attention budget" that depletes as context grows.

**Position Encoding and Context Extension**
Position encoding interpolation allows models to handle longer sequences by adapting them to originally trained smaller contexts. However, this adaptation introduces degradation in token position understanding. Models remain highly capable at longer contexts but show reduced precision for information retrieval and long-range reasoning compared to performance on shorter contexts.

**The Progressive Disclosure Principle**
Progressive disclosure manages context efficiently by loading information only as needed. At startup, agents load only skill names and descriptions--sufficient to know when a skill might be relevant. Full content loads only when a skill is activated for specific tasks.

This approach keeps agents fast while giving them access to more context on demand. The principle applies at multiple levels: skill selection, document loading, and even tool result retrieval.

### Context Quality Versus Context Quantity

The assumption that larger context windows solve memory problems has been empirically debunked. Context engineering means finding the smallest possible set of high-signal tokens that maximize the likelihood of desired outcomes.

Several factors create pressure for context efficiency. Processing cost grows disproportionately with context length--not just double the cost for double the tokens, but exponentially more in time and computing resources. Model performance degrades beyond certain context lengths even when the window technically supports more tokens. Long inputs remain expensive even with prefix caching.

The guiding principle is informativity over exhaustiveness. Include what matters for the decision at hand, exclude what does not, and design systems that can access additional information on demand.

### Context as Finite Resource

Context must be treated as a finite resource with diminishing marginal returns. Like humans with limited working memory, language models have an attention budget drawn on when parsing large volumes of context.

Every new token introduced depletes this budget by some amount. This creates the need for careful curation of available tokens. The engineering problem is optimizing utility against inherent constraints.

Context engineering is iterative and the curation phase happens each time you decide what to pass to the model. It is not a one-time prompt writing exercise but an ongoing discipline of context management.

## Practical Guidance

### File-System-Based Access

Agents with filesystem access can use progressive disclosure naturally. Store reference materials, documentation, and data externally. Load files only when needed using standard filesystem operations. This pattern avoids stuffing context with information that may not be relevant.

The file system itself provides structure that agents can navigate. File sizes suggest complexity; naming conventions hint at purpose; timestamps serve as proxies for relevance. Metadata of file references provides a mechanism to efficiently refine behavior.

### Hybrid Strategies

The most effective agents employ hybrid strategies. Pre-load some context for speed (like CLAUDE.md files or project rules), but enable autonomous exploration for additional context as needed. The decision boundary depends on task characteristics and context dynamics.

For contexts with less dynamic content, pre-loading more upfront makes sense. For rapidly changing or highly specific information, just-in-time loading avoids stale context.

### Context Budgeting

Design with explicit context budgets in mind. Know the effective context limit for your model and task. Monitor context usage during development. Implement compaction triggers at appropriate thresholds. Design systems assuming context will degrade rather than hoping it will not.

Effective context budgeting requires understanding not just raw token counts but also attention distribution patterns. The middle of context receives less attention than the beginning and end. Place critical information at attention-favored positions.

## Examples

**Example 1: Organizing System Prompts**
```markdown
<BACKGROUND_INFORMATION>
You are a Python expert helping a development team.
Current project: Data processing pipeline in Python 3.9+
</BACKGROUND_INFORMATION>

<INSTRUCTIONS>
- Write clean, idiomatic Python code
- Include type hints for function signatures
- Add docstrings for public functions
- Follow PEP 8 style guidelines
</INSTRUCTIONS>

<TOOL_GUIDANCE>
Use bash for shell operations, python for code tasks.
File operations should use pathlib for cross-platform compatibility.
</TOOL_GUIDANCE>

<OUTPUT_DESCRIPTION>
Provide actionable feedback with specific line references.
Explain the reasoning behind suggestions.
</OUTPUT_DESCRIPTION>
```

**Example 2: Progressive Document Loading**
```markdown
# Instead of loading all documentation at once:

# Step 1: Load summary
docs/architecture_overview.md     # Lightweight overview

# Step 2: Load specific section as needed
docs/api/endpoints.md             # Only when API work needed
docs/database/schemas.md          # Only when data layer work needed
```

**Example 3: Skill Description Design**
```markdown
# Bad: Vague description that loads into context but provides little signal
description: Helps with code things

# Good: Specific description that helps model decide when to activate
description: Analyze code quality and suggest refactoring patterns. Use when reviewing pull requests or improving existing code structure.
```

## Guidelines

1. Treat context as a finite resource with diminishing returns
2. Place critical information at attention-favored positions (beginning and end)
3. Use progressive disclosure to defer loading until needed
4. Organize system prompts with clear section boundaries
5. Monitor context usage during development
6. Implement compaction triggers at 70-80% utilization
7. Design for context degradation rather than hoping to avoid it
8. Prefer smaller high-signal context over larger low-signal context

# Context Degradation Patterns

Language models exhibit predictable degradation patterns as context length increases. Understanding these patterns is essential for diagnosing failures and designing resilient systems. Context degradation is not a binary state but a continuum of performance degradation that manifests in several distinct ways.

## Core Concepts

Context degradation manifests through several distinct patterns. The lost-in-middle phenomenon causes information in the center of context to receive less attention. Context poisoning occurs when errors compound through repeated reference. Context distraction happens when irrelevant information overwhelms relevant content. Context confusion arises when the model cannot determine which context applies. Context clash develops when accumulated information directly conflicts.

These patterns are predictable and can be mitigated through architectural patterns like compaction, masking, partitioning, and isolation.

## Detailed Topics

### The Lost-in-Middle Phenomenon

The most well-documented degradation pattern is the "lost-in-middle" effect, where models demonstrate U-shaped attention curves. Information at the beginning and end of context receives reliable attention, while information buried in the middle suffers from dramatically reduced recall accuracy.

**Empirical Evidence**
Research demonstrates that relevant information placed in the middle of context experiences 10-40% lower recall accuracy compared to the same information at the beginning or end. This is not a failure of the model but a consequence of attention mechanics and training data distributions.

Models allocate massive attention to the first token (often the BOS token) to stabilize internal states. This creates an "attention sink" that soaks up attention budget. As context grows, the limited budget is stretched thinner, and middle tokens fail to garner sufficient attention weight for reliable retrieval.

**Practical Implications**
Design context placement with attention patterns in mind. Place critical information at the beginning or end of context. Consider whether information will be queried directly or needs to support reasoning--if the latter, placement matters less but overall signal quality matters more.

For long documents or conversations, use summary structures that surface key information at attention-favored positions. Use explicit section headers and transitions to help models navigate structure.

### Context Poisoning

Context poisoning occurs when hallucinations, errors, or incorrect information enters context and compounds through repeated reference. Once poisoned, context creates feedback loops that reinforce incorrect beliefs.

**How Poisoning Occurs**
Poisoning typically enters through three pathways. First, tool outputs may contain errors or unexpected formats that models accept as ground truth. Second, retrieved documents may contain incorrect or outdated information that models incorporate into reasoning. Third, model-generated summaries or intermediate outputs may introduce hallucinations that persist in context.

The compounding effect is severe. If an agent's goals section becomes poisoned, it develops strategies that take substantial effort to undo. Each subsequent decision references the poisoned content, reinforcing incorrect assumptions.

**Detection and Recovery**
Watch for symptoms including degraded output quality on tasks that previously succeeded, tool misalignment where agents call wrong tools or parameters, and hallucinations that persist despite correction attempts. When these symptoms appear, consider context poisoning.

Recovery requires removing or replacing poisoned content. This may involve truncating context to before the poisoning point, explicitly noting the poisoning in context and asking for re-evaluation, or restarting with clean context and preserving only verified information.

### Context Distraction

Context distraction emerges when context grows so long that models over-focus on provided information at the expense of their training knowledge. The model attends to everything in context regardless of relevance, and this creates pressure to use provided information even when internal knowledge is more accurate.

**The Distractor Effect**
Research shows that even a single irrelevant document in context reduces performance on tasks involving relevant documents. Multiple distractors compound degradation. The effect is not about noise in absolute terms but about attention allocation--irrelevant information competes with relevant information for limited attention budget.

Models do not have a mechanism to "skip" irrelevant context. They must attend to everything provided, and this obligation creates distraction even when the irrelevant information is clearly not useful.

**Mitigation Strategies**
Mitigate distraction through careful curation of what enters context. Apply relevance filtering before loading retrieved documents. Use namespacing and organization to make irrelevant sections easy to ignore structurally. Consider whether information truly needs to be in context or can be accessed through tool calls instead.

### Context Confusion

Context confusion arises when irrelevant information influences responses in ways that degrade quality. This is related to distraction but distinct--confusion concerns the influence of context on model behavior rather than attention allocation.

If you put something in context, the model has to pay attention to it. The model may incorporate irrelevant information, use inappropriate tool definitions, or apply constraints that came from different contexts. Confusion is especially problematic when context contains multiple task types or when switching between tasks within a single session.

**Signs of Confusion**
Watch for responses that address the wrong aspect of a query, tool calls that seem appropriate for a different task, or outputs that mix requirements from multiple sources. These indicate confusion about what context applies to the current situation.

**Architectural Solutions**
Architectural solutions include explicit task segmentation where different tasks get different context windows, clear transitions between task contexts, and state management that isolates context for different objectives.

### Context Clash

Context clash develops when accumulated information directly conflicts, creating contradictory guidance that derails reasoning. This differs from poisoning where one piece of information is incorrect--in clash, multiple correct pieces of information contradict each other.

**Sources of Clash**
Clash commonly arises from multi-source retrieval where different sources have contradictory information, version conflicts where outdated and current information both appear in context, and perspective conflicts where different viewpoints are valid but incompatible.

**Resolution Approaches**
Resolution approaches include explicit conflict marking that identifies contradictions and requests clarification, priority rules that establish which source takes precedence, and version filtering that excludes outdated information from context.

### Counterintuitive Findings

Research reveals several counterintuitive patterns that challenge assumptions about context management.

**Shuffled Haystacks Outperform Coherent Ones**
Studies found that shuffled (incoherent) haystacks produce better performance than logically coherent ones. This suggests that coherent context may create false associations that confuse retrieval, while incoherent context forces models to rely on exact matching.

**Single Distractors Have Outsized Impact**
Even a single irrelevant document reduces performance significantly. The effect is not proportional to the amount of noise but follows a step function where the presence of any distractor triggers degradation.

**Needle-Question Similarity Correlation**
Lower similarity between needle and question pairs shows faster degradation with context length. Tasks requiring inference across dissimilar content are particularly vulnerable.

### When Larger Contexts Hurt

Larger context windows do not uniformly improve performance. In many cases, larger contexts create new problems that outweigh benefits.

**Performance Degradation Curves**
Models exhibit non-linear degradation with context length. Performance remains stable up to a threshold, then degrades rapidly. The threshold varies by model and task complexity. For many models, meaningful degradation begins around 8,000-16,000 tokens even when context windows support much larger sizes.

**Cost Implications**
Processing cost grows disproportionately with context length. The cost to process a 400K token context is not double the cost of 200K--it increases exponentially in both time and computing resources. For many applications, this makes large-context processing economically impractical.

**Cognitive Load Metaphor**
Even with an infinite context, asking a single model to maintain consistent quality across dozens of independent tasks creates a cognitive bottleneck. The model must constantly switch context between items, maintain a comparative framework, and ensure stylistic consistency. This is not a problem that more context solves.

## Practical Guidance

### The Four-Bucket Approach

Four strategies address different aspects of context degradation:

**Write**: Save context outside the window using scratchpads, file systems, or external storage. This keeps active context lean while preserving information access.

**Select**: Pull relevant context into the window through retrieval, filtering, and prioritization. This addresses distraction by excluding irrelevant information.

**Compress**: Reduce tokens while preserving information through summarization, abstraction, and observation masking. This extends effective context capacity.

**Isolate**: Split context across sub-agents or sessions to prevent any single context from growing large enough to degrade. This is the most aggressive strategy but often the most effective.

### Architectural Patterns

Implement these strategies through specific architectural patterns. Use just-in-time context loading to retrieve information only when needed. Use observation masking to replace verbose tool outputs with compact references. Use sub-agent architectures to isolate context for different tasks. Use compaction to summarize growing context before it exceeds limits.

## Examples

**Example 1: Detecting Degradation in Prompt Design**
```markdown
# Signs your command/skill prompt may be too large:

Early signs (context ~50-70% utilized):
- Agent occasionally misses instructions
- Responses become less focused
- Some guidelines ignored

Warning signs (context ~70-85% utilized):
- Inconsistent behavior across runs
- Agent "forgets" earlier instructions
- Quality varies significantly

Critical signs (context >85% utilized):
- Agent ignores key constraints
- Hallucinations increase
- Task completion fails
```

**Example 2: Mitigating Lost-in-Middle in Prompt Structure**
```markdown
# Organize prompts with critical info at edges

<CRITICAL_CONSTRAINTS>                    # At start (high attention)
- Never modify production files directly
- Always run tests before committing
- Maximum file size: 500 lines
</CRITICAL_CONSTRAINTS>

<DETAILED_GUIDELINES>                     # Middle (lower attention)
- Code style preferences
- Documentation templates
- Review checklists
- Example patterns
</DETAILED_GUIDELINES>

<KEY_REMINDERS>                           # At end (high attention)
- Run tests: npm test
- Format code: npm run format
- Create PR with description
</KEY_REMINDERS>
```

**Example 3: Sub-Agent Context Isolation**
```markdown
# Instead of one agent handling everything:

## Coordinator Agent (lean context)
- Understands task decomposition
- Delegates to specialized sub-agents
- Synthesizes results

## Code Review Sub-Agent (isolated context)
- Loaded only with code review guidelines
- Focuses solely on review task
- Returns structured findings

## Test Writer Sub-Agent (isolated context)
- Loaded only with testing patterns
- Focuses solely on test creation
- Returns test files
```

## Guidelines

1. Monitor context length and performance correlation during development
2. Place critical information at beginning or end of context
3. Implement compaction triggers before degradation becomes severe
4. Validate retrieved documents for accuracy before adding to context
5. Use versioning to prevent outdated information from causing clash
6. Segment tasks to prevent context confusion across different objectives
7. Design for graceful degradation rather than assuming perfect conditions
8. Test with progressively larger contexts to find degradation thresholds

# Context Degradation Patterns: Multi-Agent Workflows

This section transforms context degradation detection and mitigation concepts into actionable multi-agent workflows for Claude Code. Use these patterns when building commands, skills, or complex agent pipelines to ensure quality and reliability.

## Hallucination Detection Workflow

Hallucinations in agent output can poison downstream context and propagate errors through multi-step workflows. This workflow detects hallucinations before they compound.

### When to Use

- After any agent completes a task that produces factual claims
- Before committing agent-generated code or documentation
- When output will be used as input for subsequent agents
- During review of long-running agent sessions

### Multi-Agent Verification Pattern

**Step 1: Generate Output**

Have the primary agent complete its task normally.

**Step 2: Extract Claims**

Spawn a verification sub-agent with this prompt:

```markdown
<TASK>
Extract all factual claims from the following output. List each claim on a separate line.
</TASK>

<FOCUS_AREAS>
- File paths and their existence
- Function/class/method names referenced
- Code behavior assertions ("this function returns X")
- External facts about APIs, libraries, or specifications
- Numerical values and metrics
</FOCUS_AREAS>

<OUTPUT_TO_ANALYZE>
{agent_output}
</OUTPUT_TO_ANALYZE>

<OUTPUT_FORMAT>
One claim per line, prefixed with category:
[PATH] /src/auth/login.ts exists
[CODE] validateCredentials() returns a boolean
[FACT] JWT tokens expire after 24 hours by default
[METRIC] The function has O(n) complexity
</OUTPUT_FORMAT>
```

**Step 3: Verify Claims**

For groups of extracted claimd, spawn a verification agent:

```markdown
<TASK>
Verify this claim by checking the actual codebase and context.
</TASK>

<CLAIM>
{claim}
</CLAIM>

<VERIFICATION_APPROACH>
- For file paths: Use file tools to check existence
- For code claims: Read the actual code and verify behavior
- For external facts: Cross-reference with documentation or web search
- For metrics: Analyze the code structure
</VERIFICATION_APPROACH>

<RESPONSE_FORMAT>
STATUS: [VERIFIED | FALSE | UNVERIFIABLE]
EVIDENCE: [What you found]
CONFIDENCE: [HIGH | MEDIUM | LOW]
</RESPONSE_FORMAT>
```

**Step 4: Calculate Poisoning Risk**

Aggregate verification results:

```
total_claims = number of claims extracted
verified_count = claims marked VERIFIED
false_count = claims marked FALSE
unverifiable_count = claims marked UNVERIFIABLE

poisoning_risk = (false_count * 2 + unverifiable_count) / total_claims
```

**Step 5: Decision Threshold**

- **Risk < 0.1**: Output is reliable, proceed normally
- **Risk 0.1-0.3**: Review flagged claims manually before proceeding
- **Risk > 0.3**: Regenerate output with more explicit grounding instructions:

```markdown
<REGENERATION_PROMPT>
Previous output contained {false_count} false claims and {unverifiable_count} unverifiable claims.

Specific issues:
{list of FALSE and UNVERIFIABLE claims with evidence}

Please regenerate your response. For each factual claim:
1. Explicitly verify it using tools before stating it
2. If you cannot verify, state "I cannot verify..." instead of asserting
3. Cite the specific file/line/source for verifiable facts
</REGENERATION_PROMPT>
```

## Lost-in-Middle Detection Workflow

Critical information buried in the middle of long prompts receives less attention. This workflow detects which parts of your prompt are at risk of being ignored by running multiple agents and verifying their outputs against the original instructions.

### When to Use

- When designing new commands or skills with long prompts
- When agents inconsistently follow instructions across runs
- Before deploying prompts to production
- During prompt optimization

### Multi-Run Verification Pattern

**Step 1: Identify Critical Instructions**

Extract all critical instructions from your prompt that the agent MUST follow:

```markdown
Critical instructions to verify:
1. "Never modify files in /production"
2. "Always run tests before committing"
3. "Use TypeScript strict mode"
4. "Maximum function length: 50 lines"
5. "Include JSDoc for public APIs"
6. "Format output as JSON"
7. "Log all file modifications"
```

**Step 2: Run Multiple Agents with Same Prompt**

Spawn 3-5 agents with the SAME prompt (the command/skill/agent being tested). Each agent runs independently with identical inputs:

```markdown
<AGENT_RUN_CONFIG>
Number of runs: 5
Prompt: {your_full_prompt_being_tested}
Task: {representative_task_that_exercises_all_instructions}

For each run, save:
- run_id: unique identifier
- agent_output: complete response from agent
- timestamp: when run completed
</AGENT_RUN_CONFIG>
```

**Step 3: Verify Each Output Against Original Prompt**

For each agent's output, spawn a NEW verification agent that checks compliance with every critical instruction:

```markdown
<VERIFICATION_AGENT_PROMPT>
<TASK>
You are a compliance verification agent. Analyze whether the agent output followed each instruction from the original prompt.
</TASK>

<ORIGINAL_PROMPT>
{the_full_prompt_being_tested}
</ORIGINAL_PROMPT>

<CRITICAL_INSTRUCTIONS>
{numbered_list_of_critical_instructions}
</CRITICAL_INSTRUCTIONS>

<AGENT_OUTPUT>
{output_from_run_N}
</AGENT_OUTPUT>

<VERIFICATION_APPROACH>
For each critical instruction:
1. Determine if the instruction was applicable to this task
2. If applicable, check whether the output complies
3. Look for both explicit violations and omissions
4. Note any partial compliance
</VERIFICATION_APPROACH>

<OUTPUT_FORMAT>
RUN_ID: {run_id}

INSTRUCTION_COMPLIANCE:
- Instruction 1: "Never modify files in /production"
  STATUS: [FOLLOWED | VIOLATED | NOT_APPLICABLE]
  EVIDENCE: {quote from output or explanation}

- Instruction 2: "Always run tests before committing"
  STATUS: [FOLLOWED | VIOLATED | NOT_APPLICABLE]
  EVIDENCE: {quote from output or explanation}

[... continue for all instructions ...]

SUMMARY:
- Instructions followed: {count}
- Instructions violated: {count}
- Not applicable: {count}
</OUTPUT_FORMAT>
</VERIFICATION_AGENT_PROMPT>
```

**Step 4: Aggregate Results and Identify At-Risk Parts**

Collect verification results from all runs and identify instructions that were inconsistently followed:

```markdown
<AGGREGATION_LOGIC>
For each instruction:
  followed_count = number of runs where STATUS == FOLLOWED
  violated_count = number of runs where STATUS == VIOLATED
  applicable_runs = total_runs - (runs where STATUS == NOT_APPLICABLE)

  compliance_rate = followed_count / applicable_runs

  Classification:
  - compliance_rate == 1.0: RELIABLE (always followed)
  - compliance_rate >= 0.8: MOSTLY_RELIABLE (minor inconsistency)
  - compliance_rate >= 0.5: AT_RISK (inconsistent - likely lost-in-middle)
  - compliance_rate < 0.5: FREQUENTLY_IGNORED (severe issue)
  - compliance_rate == 0.0: ALWAYS_IGNORED (critical failure)

AT_RISK instructions are the primary signal for lost-in-middle problems.
These are instructions that work sometimes but not consistently, indicating
they are in attention-weak positions.
</AGGREGATION_LOGIC>

<AGGREGATION_OUTPUT_FORMAT>
INSTRUCTION COMPLIANCE SUMMARY:

| Instruction | Followed | Violated | Compliance Rate | Status |
|-------------|----------|----------|-----------------|--------|
| 1. Never modify /production | 5/5 | 0/5 | 100% | RELIABLE |
| 2. Run tests before commit | 3/5 | 2/5 | 60% | AT_RISK |
| 3. TypeScript strict mode | 4/5 | 1/5 | 80% | MOSTLY_RELIABLE |
| 4. Max function length 50 | 2/5 | 3/5 | 40% | FREQUENTLY_IGNORED |
| 5. Include JSDoc | 5/5 | 0/5 | 100% | RELIABLE |
| 6. Format as JSON | 1/5 | 4/5 | 20% | ALWAYS_IGNORED |
| 7. Log modifications | 3/5 | 2/5 | 60% | AT_RISK |

AT-RISK INSTRUCTIONS (likely in lost-in-middle zone):
- Instruction 2: "Run tests before commit" (60% compliance)
- Instruction 4: "Max function length 50" (40% compliance)
- Instruction 6: "Format as JSON" (20% compliance)
- Instruction 7: "Log modifications" (60% compliance)
</AGGREGATION_OUTPUT_FORMAT>
```

**Step 5: Output Recommendations**

Based on the at-risk parts identified, provide specific remediation guidance:

```markdown
<RECOMMENDATIONS_OUTPUT>
LOST-IN-MIDDLE ANALYSIS COMPLETE

At-Risk Instructions Detected: {count}
These instructions are inconsistently followed, indicating they likely
reside in attention-weak positions (middle of prompt).

SPECIFIC RECOMMENDATIONS:

1. MOVE CRITICAL INFORMATION TO ATTENTION-FAVORED POSITIONS
   The following instructions should be relocated to the beginning or end of your prompt:
   - "Run tests before commit" -> Move to <CRITICAL_CONSTRAINTS> at prompt START
   - "Max function length 50" -> Move to <KEY_REMINDERS> at prompt END
   - "Format as JSON" -> Move to <OUTPUT_FORMAT> at prompt END
   - "Log modifications" -> Add to both START and END sections

2. USE EXPLICIT MARKERS TO HIGHLIGHT CRITICAL INFORMATION
   Restructure at-risk instructions with emphasis:

   Before: "Always run tests before committing"
   After:  "**CRITICAL:** You MUST run tests before committing. Never skip this step."

   Before: "Maximum function length: 50 lines"
   After:  "3. [REQUIRED] Maximum function length: 50 lines"

   Use numbered lists, bold markers, or explicit tags like [REQUIRED], [CRITICAL], [MUST].

3. CONSIDER SPLITTING CONTEXT TO REDUCE MIDDLE SECTION
   If your prompt has many instructions, consider:
   - Breaking into focused sub-prompts for different aspects
   - Using sub-agents with specialized, shorter contexts
   - Moving detailed guidance to on-demand sections loaded only when needed

   Current prompt structure creates a large middle section where
   {count} instructions are being lost. Reduce middle section by:
   - Moving 2-3 most critical items to edges
   - Converting remaining middle items to a numbered checklist
   - Adding explicit "verify these items" reminder at end
</RECOMMENDATIONS_OUTPUT>
```

### Complete Workflow Example

```markdown
# Example: Testing a Code Review Command

## Original Prompt Being Tested:
"Review the code for: security issues, performance problems,
code style, test coverage, documentation completeness,
error handling, and logging practices."

## Run 5 Agents:
Each agent reviews the same code sample with this prompt.

## Verification Results:
| Instruction | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Rate |
|-------------|-------|-------|-------|-------|-------|------|
| Security | Y | Y | Y | Y | Y | 100% |
| Performance | Y | X | Y | X | Y | 60% |
| Code style | X | X | Y | X | X | 20% |
| Test coverage | X | Y | X | X | Y | 40% |
| Documentation | X | X | X | Y | X | 20% |
| Error handling | Y | Y | X | Y | Y | 80% |
| Logging | Y | Y | Y | Y | Y | 100% |

## Analysis:
- RELIABLE: Security, Logging (at edges of list)
- AT_RISK: Performance, Error handling
- FREQUENTLY_IGNORED: Code style, Test coverage, Documentation (middle of list)

## Remediation Applied:
"**CRITICAL REVIEW AREAS:**
1. Security vulnerabilities
2. Test coverage gaps
3. Documentation completeness

Review also: performance, code style, error handling, logging.

**BEFORE COMPLETING:** Verify you addressed items 1-3 above."
```

## Error Propagation Analysis Workflow

In multi-agent chains, errors from early agents propagate and amplify through subsequent agents. This workflow traces errors to their source.

### When to Use

- When final output contains errors despite correct intermediate steps
- When debugging complex multi-agent workflows
- When establishing error boundaries in agent chains
- During post-mortem analysis of failed agent tasks

### Error Trace Pattern

**Step 1: Capture Agent Chain Outputs**

Record the output of each agent in your chain:

```markdown
Agent Chain Record:
- Agent 1 (Analyzer): {output_1}
- Agent 2 (Planner): {output_2}
- Agent 3 (Implementer): {output_3}
- Agent 4 (Reviewer): {output_4}
```

**Step 2: Identify Error Symptoms**

Spawn an error identification agent:

```markdown
<TASK>
Analyze the final output and identify all errors, inconsistencies, or quality issues.
</TASK>

<FINAL_OUTPUT>
{output_from_last_agent}
</FINAL_OUTPUT>

<OUTPUT_FORMAT>
ERROR_ID: E1
DESCRIPTION: Function missing null check
LOCATION: src/utils/parser.ts:45
SEVERITY: HIGH

ERROR_ID: E2
...
</OUTPUT_FORMAT>
```

**Step 3: Trace Each Error Backward**

For each identified error, spawn a trace agent:

```markdown
<TASK>
Trace this error backward through the agent chain to find its origin.
</TASK>

<ERROR>
{error_description}
</ERROR>

<AGENT_CHAIN_OUTPUTS>
Agent 1 Output: {output_1}
Agent 2 Output: {output_2}
Agent 3 Output: {output_3}
Agent 4 Output: {output_4}
</AGENT_CHAIN_OUTPUTS>

<ANALYSIS_APPROACH>
For each agent output (starting from the last):
1. Does this output contain the error?
2. If yes, was the error present in the input to this agent?
3. If error is in output but not input: This agent INTRODUCED the error
4. If error is in both: This agent PROPAGATED the error
</ANALYSIS_APPROACH>

<OUTPUT_FORMAT>
ERROR: {error_id}
ORIGIN_AGENT: Agent {N}
ORIGIN_TYPE: [INTRODUCED | PROPAGATED_FROM_CONTEXT | PROPAGATED_FROM_TOOL_OUTPUT]
ROOT_CAUSE: {explanation}
CONTEXT_THAT_CAUSED_IT: {relevant context snippet if applicable}
</OUTPUT_FORMAT>
```

**Step 4: Calculate Propagation Metrics**

```
For each agent in chain:
  errors_introduced = count of errors this agent created
  errors_propagated = count of errors this agent passed through
  errors_caught = count of errors this agent fixed or flagged

propagation_rate = errors_at_end / errors_introduced_total
amplification_factor = errors_at_end / errors_at_start
```

**Step 5: Establish Error Boundaries**

Based on analysis, add verification checkpoints:

```markdown
<ERROR_BOUNDARY_TEMPLATE>
After Agent {N} completes:

1. Spawn verification agent to check for common error patterns:
   - {error_pattern_1 that Agent N tends to introduce}
   - {error_pattern_2 that Agent N tends to introduce}

2. If errors detected:
   - Log error for analysis
   - Either: Fix inline and continue
   - Or: Regenerate Agent N output with explicit guidance

3. Only proceed to Agent {N+1} if verification passes
</ERROR_BOUNDARY_TEMPLATE>
```

## Context Relevance Scoring Workflow

Not all parts of a prompt contribute equally to task completion. This workflow identifies distractor parts within a prompt that consume attention budget without adding value.

### When to Use

- When optimizing prompt length and content
- When deciding what to include in CLAUDE.md
- When a prompt feels bloated but you are unsure what to cut
- When debugging agents that ignore provided context
- Before deploying new commands, skills, or agent prompts

### Distractor Identification Pattern

**Step 1: Split Prompt into Parts**

Divide the prompt (command/skill/agent) into logical sections. Each part should be a coherent unit:

```markdown
<PROMPT_PARTS>
PART_1:
  ID: background
  CONTENT: |
    You are a Python expert helping a development team.
    Current project: Data processing pipeline in Python 3.9+

PART_2:
  ID: code_style_rules
  CONTENT: |
    - Write clean, idiomatic Python code
    - Include type hints for function signatures
    - Add docstrings for public functions
    - Follow PEP 8 style guidelines

PART_3:
  ID: historical_context
  CONTENT: |
    The project was migrated from Python 2.7 in 2019.
    Original team used camelCase naming but we now use snake_case.
    Legacy modules in /legacy folder are frozen.

PART_4:
  ID: output_format
  CONTENT: |
    Provide actionable feedback with specific line references.
    Explain the reasoning behind suggestions.
</PROMPT_PARTS>
```

Splitting guidelines:
- Each XML section or Markdown header becomes a part
- Separate conceptually distinct instructions into their own parts
- Keep related instructions together (do not split mid-thought)
- Aim for 3-15 parts depending on prompt length

**Step 2: Spawn Scoring Agents**

Spawn multiple scoring agents in parallel:

```markdown
<TASK>
Score how relevant this prompt parts is for accomplishing the specified task.
</TASK>

<TASK_DESCRIPTION>
{description of what the agent should accomplish}
Example: "Review a pull request for code quality issues and suggest improvements"
</TASK_DESCRIPTION>

<PROMPT_PARTS>
{contents of all the parts being evaluated}
</PROMPT_PARTS>

<SCORING_CRITERIA>
Score 0-10 based on these criteria:

ESSENTIAL (8-10):
- Part directly enables task completion
- Removing this part would cause task failure
- Part contains critical constraints that prevent errors
- Part defines required output format or structure

HELPFUL (5-7):
- Part improves output quality but is not strictly required
- Part provides useful context that guides better decisions
- Part contains preferences that affect style but not correctness

MARGINAL (2-4):
- Part has tangential relevance to the task
- Part might occasionally be useful but usually is not
- Part provides historical context rarely needed

DISTRACTOR (0-1):
- Part is irrelevant to the task
- Part could confuse the agent about what to focus on
- Part competes for attention without contributing value
</SCORING_CRITERIA>

<OUTPUT_FORMAT>
RELEVANCE_SCORE: [0-10]
JUSTIFICATION: [2-3 sentences explaining the score]
USAGE_LIKELIHOOD: [How often would the agent reference this part during task execution? ALWAYS | OFTEN | SOMETIMES | RARELY | NEVER]
</OUTPUT_FORMAT>
```

**Step 3: Aggregate Relevance Scores**

Collect scores from all scoring agents:

```
PART_SCORES = [
  {id: "background", score: 8, usage: "ALWAYS"},
  {id: "code_style_rules", score: 9, usage: "ALWAYS"},
  {id: "historical_context", score: 3, usage: "RARELY"},
  {id: "output_format", score: 7, usage: "OFTEN"}
]
```

Calculate aggregate metrics:

```
total_parts = count(PART_SCORES)
high_relevance_parts = count(parts where score >= 5)
distractor_parts = count(parts where score < 5)

context_efficiency = high_relevance_parts / total_parts
average_relevance = sum(scores) / total_parts
```

**Step 4: Identify Distractor Parts**

Apply the distractor threshold (score < 5):

```markdown
DISTRACTOR_ANALYSIS:

Identified Distractors:
1. PART: historical_context
   SCORE: 3/10
   JUSTIFICATION: "Migration history from Python 2.7 is rarely relevant to reviewing current code. The naming convention note is useful but should be in code_style_rules instead."
   RECOMMENDATION: REMOVE or RELOCATE

Summary:
- Total parts: 4
- High-relevance parts (>=5): 3
- Distractor parts (<5): 1
- Context efficiency: 75%
- Average relevance: 6.75

Token Impact:
- Distractor tokens: ~45 (historical_context)
- Potential savings: 45 tokens (11% of prompt)
```

**Step 5: Generate Optimization Recommendations**

Based on distractor analysis, provide actionable recommendations:

```markdown
OPTIMIZATION_RECOMMENDATIONS:

1. REMOVE: historical_context
   Reason: Score 3/10, usage RARELY. Migration history does not inform code review decisions.

2. RELOCATE: "we now use snake_case" from historical_context
   Target: code_style_rules section
   Reason: This specific rule is relevant but buried in irrelevant historical context.

3. CONSIDER CONDENSING: background
   Current: 2 sentences
   Could be: 1 sentence ("Python 3.9+ data pipeline expert")
   Savings: ~15 tokens

OPTIMIZED PROMPT STRUCTURE:
- background (condensed): 8 tokens
- code_style_rules (with snake_case added): 52 tokens
- output_format: 28 tokens
- Total: 88 tokens (down from 133 tokens)
- Efficiency improvement: 34% reduction
```

### Distractor Threshold Guidelines

The default threshold of 5 balances comprehensiveness against efficiency:

| Threshold | Use Case |
|-----------|----------|
| < 3 | Aggressive pruning for token-constrained contexts |
| < 5 | Standard optimization (recommended default) |
| < 7 | Conservative pruning for critical prompts |

Adjust threshold based on:
- **Context budget pressure**: Lower threshold when approaching limits
- **Task criticality**: Higher threshold for production prompts
- **Prompt stability**: Lower threshold for experimental prompts

### Scoring Agent Deployment

For efficiency, parallelize scoring agents:

```markdown
# Parallel execution pattern
spawn_parallel([
  scoring_agent(part_1, task_description),
  scoring_agent(part_2, task_description),
  scoring_agent(part_3, task_description),
  ...
])

# Collect and aggregate
scores = await_all(scoring_agents)
analysis = aggregate_scores(scores)
```

For large prompts (>10 parts), batch scoring agents in groups of 5-7 to manage orchestration overhead.

## Context Health Monitoring Workflow

Long-running agent sessions accumulate context that degrades over time. This workflow monitors context health and triggers intervention.

### When to Use

- During long-running agent sessions (>20 turns)
- When agents start exhibiting degradation symptoms
- As a periodic health check in agent orchestration systems
- Before critical decision points in agent workflows

### Health Check Pattern

**Step 1: Periodic Symptom Detection**

Every N turns (recommended: every 10 turns), spawn a health check agent:

```markdown
<TASK>
Analyze the recent conversation history for signs of context degradation.
</TASK>

<RECENT_HISTORY>
{last 10 turns of conversation}
</RECENT_HISTORY>

<SYMPTOM_CHECKLIST>
Check for these degradation symptoms:

LOST_IN_MIDDLE:
- [ ] Agent missing instructions from early in conversation
- [ ] Critical constraints being ignored
- [ ] Agent asking for information already provided

CONTEXT_POISONING:
- [ ] Same error appearing repeatedly
- [ ] Agent referencing incorrect information as fact
- [ ] Hallucinations that persist despite correction

CONTEXT_DISTRACTION:
- [ ] Responses becoming unfocused
- [ ] Agent using irrelevant context inappropriately
- [ ] Quality declining on previously-successful tasks

CONTEXT_CONFUSION:
- [ ] Agent mixing up different task requirements
- [ ] Wrong tool selections for obvious tasks
- [ ] Outputs that blend requirements from different tasks

CONTEXT_CLASH:
- [ ] Agent expressing uncertainty about conflicting information
- [ ] Inconsistent behavior between turns
- [ ] Agent asking for clarification on resolved issues
</SYMPTOM_CHECKLIST>

<OUTPUT_FORMAT>
HEALTH_STATUS: [HEALTHY | DEGRADED | CRITICAL]
SYMPTOMS_DETECTED: [list of checked symptoms]
RECOMMENDED_ACTION: [CONTINUE | COMPACT | RESTART]
SPECIFIC_ISSUES: [detailed description of problems found]
</OUTPUT_FORMAT>
```

**Step 2: Automated Intervention**

Based on health status, trigger appropriate intervention:

```markdown
IF HEALTH_STATUS == "DEGRADED" or HEALTH_STATUS == "CRITICAL":
  <RESTART_INTERVENTION>
  1. Extract essential state to preserve and save to a file
  2. Ask user to start a new session with clean context and load the preserved state from the file after the new session is started
  </RESTART_INTERVENTION>
```

## Guidelines for Multi-Agent Verification

1. Spawn verification agents with focused, single-purpose prompts
2. Use structured output formats for reliable parsing
3. Set clear thresholds for action vs. continue decisions
4. Log all verification results for debugging and optimization
5. Balance verification overhead against error prevention value
6. Implement verification at natural checkpoints, not every turn
7. Use lighter-weight checks for routine operations, heavier for critical ones
8. Design verification to be skippable in time-critical scenarios

# Context Optimization Techniques

Context optimization extends the effective capacity of limited context windows through strategic compression, masking, caching, and partitioning. The goal is not to magically increase context windows but to make better use of available capacity. Effective optimization can double or triple effective context capacity without requiring larger models or longer contexts.

## Core Concepts

Context optimization extends effective capacity through four primary strategies: compaction (summarizing context near limits), observation masking (replacing verbose outputs with references), KV-cache optimization (reusing cached computations), and context partitioning (splitting work across isolated contexts).

The key insight is that context quality matters more than quantity. Optimization preserves signal while reducing noise. The art lies in selecting what to keep versus what to discard, and when to apply each technique.

## Detailed Topics

### Compaction Strategies

**What is Compaction**
Compaction is the practice of summarizing context contents when approaching limits, then reinitializing a new context window with the summary. This distills the contents of a context window in a high-fidelity manner, enabling the agent to continue with minimal performance degradation.

Compaction typically serves as the first lever in context optimization. The art lies in selecting what to keep versus what to discard.

**Compaction in Practice**
Compaction works by identifying sections that can be compressed, generating summaries that capture essential points, and replacing full content with summaries. Priority for compression:

1. **Tool outputs** - Replace verbose outputs with key findings
2. **Old conversation turns** - Summarize early exchanges
3. **Retrieved documents** - Summarize if task context captured
4. **Never compress** - System prompt and critical constraints

**Summary Generation**
Effective summaries preserve different elements depending on content type:

- **Tool outputs**: Preserve key findings, metrics, and conclusions. Remove verbose raw output.
- **Conversational turns**: Preserve key decisions, commitments, and context shifts. Remove filler and back-and-forth.
- **Retrieved documents**: Preserve key facts and claims. Remove supporting evidence and elaboration.

### Observation Masking

**The Observation Problem**
Tool outputs can comprise 80%+ of token usage in agent trajectories. Much of this is verbose output that has already served its purpose. Once an agent has used a tool output to make a decision, keeping the full output provides diminishing value while consuming significant context.

Observation masking replaces verbose tool outputs with compact references. The information remains accessible if needed but does not consume context continuously.

**Masking Strategy Selection**
Not all observations should be masked equally:

**Never mask:**
- Observations critical to current task
- Observations from the most recent turn
- Observations used in active reasoning

**Consider masking:**
- Observations from 3+ turns ago
- Verbose outputs with key points extractable
- Observations whose purpose has been served

**Always mask:**
- Repeated outputs
- Boilerplate headers/footers
- Outputs already summarized in conversation

### Context Partitioning

**Sub-Agent Partitioning**
The most aggressive form of context optimization is partitioning work across sub-agents with isolated contexts. Each sub-agent operates in a clean context focused on its subtask without carrying accumulated context from other subtasks.

This approach achieves separation of concerns--the detailed search context remains isolated within sub-agents while the coordinator focuses on synthesis and analysis.

**When to Partition**
Consider partitioning when:
- Task naturally decomposes into independent subtasks
- Different subtasks require different specialized context
- Context accumulation threatens to exceed limits
- Different subtasks have conflicting requirements

**Result Aggregation**
Aggregate results from partitioned subtasks by:
1. Validating all partitions completed
2. Merging compatible results
3. Summarizing if combined results still too large
4. Resolving conflicts between partition outputs


## Practical Guidance

### Optimization Decision Framework

**When to optimize:**
- Response quality degrades as conversations extend
- Costs increase due to long contexts
- Latency increases with conversation length

**What to apply:**
- Tool outputs dominate: observation masking
- Retrieved documents dominate: summarization or partitioning
- Message history dominates: compaction with summarization
- Multiple components: combine strategies

### Applying Optimization to Claude Code Prompts

**Command Optimization**
Commands load on-demand, so focus on keeping individual commands focused:
```markdown
# Good: Focused command with clear scope
---
name: review-security
description: Review code for security vulnerabilities
---
# Specific security review instructions only

# Avoid: Overloaded command trying to do everything
---
name: review-all
description: Review code for everything
---
# 50 different review checklists crammed together
```

**Skill Optimization**
Skills load their descriptions by default, so descriptions must be concise:
```markdown
# Good: Concise description
description: Analyze code architecture. Use for design reviews.

# Avoid: Verbose description that wastes context budget
description: This skill provides comprehensive analysis of code
architecture including but not limited to class hierarchies,
dependency graphs, coupling metrics, cohesion analysis...
```

**Sub-Agent Context Design**
When spawning sub-agents, provide focused context:
```markdown
# Coordinator provides minimal handoff:
"Review authentication module for security issues.
Return findings in structured format."

# NOT this verbose handoff:
"I need you to look at the authentication module which is
located in src/auth/ and contains several files including
login.ts, session.ts, tokens.ts... [500 more tokens of context]"
```

## Guidelines

1. Measure before optimizing--know your current state
2. Apply compaction before masking when possible
3. Design for cache stability with consistent prompts
4. Partition before context becomes problematic
5. Monitor optimization effectiveness over time
6. Balance token savings against quality preservation
7. Test optimization at production scale
8. Implement graceful degradation for edge cases
