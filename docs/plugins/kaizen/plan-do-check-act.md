# /plan-do-check-act - PDCA Improvement Cycle

Four-phase iterative cycle for continuous improvement through systematic experimentation: Plan, Do, Check, Act.

- Purpose - Structured approach to measured, sustainable improvements
- Output - PDCA cycle documentation with baseline, hypothesis, results, and next steps

```bash
/plan-do-check-act ["improvement goal"]
```

## Arguments

Optional improvement goal or problem to address. If not provided, you will be prompted for input.

## How It Works

**Phase 1: PLAN**
1. Define the problem or improvement goal
2. Analyze current state (baseline metrics)
3. Identify root causes (use /why or /cause-and-effect)
4. Develop hypothesis: "If we change X, Y will improve"
5. Design experiment: what to change, how to measure
6. Set success criteria (measurable targets)

**Phase 2: DO**
1. Implement the planned change (small scale first)
2. Document what was actually done
3. Record any deviations from plan
4. Collect data throughout implementation
5. Note unexpected observations

**Phase 3: CHECK**
1. Measure results against success criteria
2. Compare to baseline (before vs. after)
3. Analyze: did hypothesis hold?
4. Identify what worked and what did not
5. Document learnings

**Phase 4: ACT**
- **If successful**: Standardize the change, update docs, train team, monitor
- **If unsuccessful**: Learn why, refine hypothesis, start new cycle
- **If partially successful**: Standardize what worked, plan next cycle for remainder

## Usage Examples

```bash
# Reduce build time
> /plan-do-check-act "Reduce Docker build from 45min to under 10min"

# Improve code quality
> /plan-do-check-act "Reduce production bugs from 8 to 4 per month"

# Speed up code review
> /plan-do-check-act "Reduce PR merge time from 3 days to 1 day"
```

**Example Cycle**:
```
CYCLE 1
───────
PLAN:
  Problem: Docker build takes 45 minutes
  Current State: Full rebuild every time, no layer caching
  Root Cause: Package manager cache not preserved between builds
  Hypothesis: Caching dependencies will reduce build to <10 minutes
  Success Criteria: Build time <10 minutes on unchanged dependencies

DO:
  - Restructured Dockerfile: COPY package*.json before src files
  - Added .dockerignore for node_modules
  - Configured CI cache for Docker layers

CHECK:
  Results:
    - Unchanged dependencies: 8 minutes (was 45)
    - Changed dependencies: 12 minutes (was 45)
  Analysis: 82% reduction on cached builds, hypothesis confirmed

ACT:
  Standardize:
    ✓ Merged Dockerfile changes
    ✓ Updated CI pipeline config
    ✓ Documented in README

  New Problem: 12 minutes still slow when deps change
  → Start CYCLE 2
```

## Best Practices

- Start small - Make measurable changes, not big overhauls
- Expect multiple cycles - PDCA is iterative; 2-3 cycles is normal
- Failed experiments are learning - Document why and adjust hypothesis
- Success criteria must be measurable - "Faster" is not a criteria; "<10 minutes" is
- Standardize successes - Document and train team on what works
- If stuck after 3 cycles - Revisit root cause analysis
