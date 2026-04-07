# Code Quality Improvement

Systematic code quality improvement using Kaizen methodology with PDCA cycles and multi-perspective analysis.

For root cause analysis of bugs and incidents, use the [Debugging and Root Cause Analysis](./debugging-root-cause.md) workflow.

## When to Use

- Performance optimization of existing code
- Technical debt reduction and cleanup
- Process bottleneck identification
- Codebase-wide quality audits
- Continuous improvement initiatives

## Plugins needed for this workflow

- [Kaizen](../plugins/kaizen/README.md)
- [Reflexion](../plugins/reflexion/README.md)
- [Code Review](../plugins/code-review/README.md)
- [Git](../plugins/git/README.md)

## Workflow

### How It Works

```md
┌─────────────────────────────────────────────┐
│ 1. Analyze Target Area                      │
│    (identify improvement opportunities)     │
└────────────────────┬────────────────────────┘
                     │
                     │ understand current state and waste
                     ▼
┌─────────────────────────────────────────────┐
│ 2. Get Multi-Perspective Critique           │
│    (comprehensive quality review)           │
└────────────────────┬────────────────────────┘
                     │
                     │ identify issues from multiple angles
                     ▼
┌─────────────────────────────────────────────┐
│ 3. Plan Improvements (PDCA Cycle)           │ ◀─── iterate if needed ───┐
│    (hypothesis + success criteria)          │                           │
└────────────────────┬────────────────────────┘                           │
                     │                                                    │
                     │ define measurable improvement plan                 │
                     ▼                                                    │
┌─────────────────────────────────────────────┐                           │
│ 4. Implement Changes                        │                           │
│    (apply optimizations)                    │                           │
└────────────────────┬────────────────────────┘                           │
                     │                                                    │
                     │ execute plan with small changes                    │
                     ▼                                                    │
┌─────────────────────────────────────────────┐                           │
│ 5. Review Changes                           │───────────────────────────┘
│    (verify quality)                         │
└────────────────────┬────────────────────────┘
                     │
                     │ validate improvements meet criteria
                     ▼
┌─────────────────────────────────────────────┐
│ 6. Preserve Learnings                       │
│    (update project memory)                  │
└────────────────────┬────────────────────────┘
                     │
                     │ save insights for future reference
                     ▼
┌─────────────────────────────────────────────┐
│ 7. Commit Changes                           │
│    (conventional commit)                    │
└─────────────────────────────────────────────┘
```

### 1. Analyze target area

Use the `/analyse` command to intelligently analyze your target area for improvement opportunities. The command auto-selects the best analysis method: Gemba Walk (code exploration), Value Stream Mapping (workflow/process), or Muda Analysis (waste identification).

```bash
/analyse Target the checkout flow for performance optimization
```

After LLM completes, review the analysis findings including identified waste, bottlenecks, or gaps between documentation and reality. The output provides actionable insights categorized by priority.

### 2. Get multi-perspective critique

Use the `/reflexion:critique` command to get comprehensive feedback from multiple specialized perspectives. This surfaces issues that might be missed by a single analysis approach.

```bash
/reflexion:critique
```

After LLM completes, review the structured feedback from multiple judges covering different aspects like security, performance, maintainability, and design. Note the consensus points and any areas of disagreement.

### 3. Plan improvements with PDCA cycle

Use the `/plan-do-check-act` command to create a structured improvement plan with measurable success criteria. This ensures changes are systematic and results can be verified.

```bash
/plan-do-check-act Reduce API response time by 50%
```

After LLM completes, review the PDCA plan which includes:
- **Plan**: Problem definition, baseline metrics, hypothesis, and success criteria
- **Do**: Specific changes to implement
- **Check**: How to measure results
- **Act**: What to do based on outcomes

You can adjust the plan before proceeding to implementation.

### 4. Implement the improvements

Apply the identified improvements to your codebase. Focus on small, incremental changes that can be measured against your success criteria.

```bash
claude "Apply the performance optimizations from the PDCA plan to the checkout flow"
```

After LLM completes, the changes are applied to your local working directory. The LLM documents what was actually done, including any deviations from the original plan and unexpected observations.

### 5. Review local changes

Use the `/review-local-changes` command to verify the quality of implemented changes before committing.

```bash
/review-local-changes
```

After LLM completes, review the findings from multiple specialized agents (Bug Hunter, Security Auditor, Code Quality Reviewer, etc.). Address any critical or high-priority issues before proceeding. If the review identifies significant problems, iterate back to step 4.

### 6. Preserve learnings

Use the `/reflexion:memorize` command to capture valuable insights from this improvement cycle for future reference.

```bash
/reflexion:memorize Performance optimization patterns for checkout flow
```

After LLM completes, the insights are added to your project's CLAUDE.md file. This builds a knowledge base of patterns, pitfalls, and solutions that improve future development.

### 7. Create conventional commit

Use the `/git:commit` command to create a well-formatted commit message following conventional commit standards.

```bash
/git:commit
```

After LLM completes, review the generated commit message which describes the improvement, its rationale, and measurable impact. The commit is ready to push to your repository.

## Alternative Analysis Commands

Depending on your improvement goal, you may want to use specialized Kaizen commands:

### For comprehensive problem documentation

Use `/analyse-problem` when you need a structured A3 one-page analysis with background, root cause, countermeasures, and implementation plan.

```bash
/analyse-problem API response times degraded after last release
```

### For iterative root cause investigation

Use `/why` (Five Whys) when you need to drill from symptoms to fundamental causes through iterative questioning.

```bash
/why Why is the checkout page loading slowly?
```

### For systematic cause exploration

Use `/cause-and-effect` (Fishbone analysis) when exploring causes across multiple categories: People, Process, Technology, Methods, Environment, and Materials.

```bash
/cause-and-effect Investigate causes of high memory usage in production
```

## Tips for Effective Quality Improvement

- **Small iterations**: Make incremental changes that can be individually verified
- **Document findings**: Use A3 format for significant issues to maintain organizational learning
- **Iterate PDCA cycles**: Multiple cycles are normal; each cycle builds on previous learnings
- **Involve the right perspective**: Use `/reflexion:critique` for important decisions
- **Preserve knowledge**: Always memorize significant insights to improve future work
- **Use automatic reflection**: Add "reflect" to prompts for automatic quality verification (e.g., `"implement optimization, reflect"`)

## Automatic Reflection with Hooks

For streamlined workflows, use the Reflexion plugin's automatic hooks. Include "reflect" in your prompt and Claude will automatically review its work:

```bash
# Automatic reflection during improvement work
> claude "Apply the performance optimizations from the PDCA plan, then reflect"
# Claude applies changes and automatically verifies quality
```

This is especially useful for:
- Quick verification after small changes
- Integrating reflection into natural workflow
- Ensuring quality without manual command steps

See [Reflexion Plugin](../plugins/reflexion/README.md) for more details.
