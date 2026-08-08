---
title: Simplify SDD workflow for long horizon tasks
---

## Initial User Prompt

### Requirements

simplify plugins/sdd/skills/plan-task workflow for long horizon tasks

#### Step 1

The plugins/sdd/agents/qa-engineer.md and plugins/sdd/agents/business-analyst.md doing esentially the same work now, but at different stages. This makes plan-task workflow is too long. But they also have some parts that other not doing, so their work not dublication, rather different angle of view.

[] Merge the qa-engineer.md and business-analyst.md into one agent -> business-analyst.md. He should perform ALL work that currently is done by qa-engineer.md AND business-analyst.md. So don't lose any steps in their workflows after combining them. It still should produce the Description as now, but acceptance criteria should be different. Agent firstly should write them in scratchbook, as it doing now. But then it should go through QA engineer processes Context Analysis -> Per-Step Checklist -> Per-Step Principles -> ... . Final results should contain. What is currently wrote in Verification section by QA Engineer (Checklist, Rubric, etc.), but in Acceptance Criteria section. The verificaition section no longer needed. 
[] CRITICAL: Acceptance Criteria from business perspective still should be written, but now only in scratchbook. Final Acceptance Criteria (checklist, rubric, etc.) should contain technical AND business criteria mixed in a way that most appropriate to define verification of task. And test apporach (Tes Strategy, Test Matrix, etc) should present there.
[] CRITICAL: Avoid summaraising or decreasing the business analytst OR QA engineer prompt. You shuold copy where possible, and change only what need.
[] While merging, adjust QA engineer process:
  [] It not longer should be done per-step, as it was before. Steps now written later in workflow, so Business Analyst (previously QA Engineer) should now focus on WHOLE task verification, rather then specific steps.
  [] Decrease QA Engineer process artifacts focus. It can still mention in his acceptance criteria artifacts, if they mentioned in user prompt, but it no longer the focus. Artifacts code/test fails can be defined by solution architect later in workflow. So QA Engineer may not know about them. Instead he must focus more on overral feature and functionality verification + test approach: Define testing strategy (unit, integration, etc), test matrix, test cases to cover, by which types of tests. So overral verification of tests can be done across all tests types at the end, no metter where they are written.
[] Remove qa-engineer.md and his mentions from plan-task workflow.

##### Step 1 — Design Decisions

- **Merged scratchpad flow** (one continuous log, copy-not-summarize): Phase 1 Requirements Discovery -> Phase 2 Concept Extraction -> Phase 3 Requirements Analysis -> Phase 4 Draft Output (business-perspective acceptance criteria drafted here and ONLY here) -> Context Analysis -> Checklist (Hard Rules + TICK) -> Principles Extraction -> Test Strategy (Decision Gates 0-6) -> Rubric Dimensions -> RRD Refinement -> Self-Verification.
- **Task-level, not step-level**: qa-engineer's `Step Inventory` becomes a task scope inventory; the `### Step N` loops in its Stages 3-8 collapse into a single pass over the whole task.
- **Artifacts demoted**: `Artifact Classification` no longer drives the process. Artifacts may be cited only when the user prompt named them, because the software-architect defines real file paths later in the workflow.
- **`Verification Level Determination` is deleted** — verification levels (None / Single Judge / Panel of 2 / Per-Item) no longer exist anywhere in the plugin.
- **No `**Threshold:**` value is written into the task file** by any agent (see Step 3 — thresholds are orchestrator config only).
- **The Acceptance Criteria section IS the checklist / regular checks / rubric.** There is no separate prose criteria list. Each of these sub-blocks mixes business and technical criteria. Final `## Acceptance Criteria` section contents, in order:
  1. `**Checklist:**` — table `| ID | Question | Category | Importance |`
  2. `**Regular Checks:**` — build / lint / tests / duplication / boy-scout / reuse / test-coverage checkboxes
  3. `**Rubric:**` — table `| Criterion | Weight |` (weights sum to 1.0)
  4. `**Rubric Score Definitions:**` — per-criterion 1-5 definitions
  5. `**Test Strategy:**` — Test Matrix table + Test Cases to Cover
  6. `Definition of Done`
- **All output stays human-readable structured markdown, never YAML** in the task file (YAML remains the scratchpad's machine-readable source of truth) — exactly as qa-engineer §9.2 already prescribes.
- **`Test Cases to Cover` groups cases under checklist item IDs** (not the old `AC-N` prose anchors), since the checklist items are now the acceptance criteria. The coverage map's "no orphans" rule means every testable checklist item has >= 1 test case.
- **Deleted from the task file format**: `#### Verification` sections and the `## Verification Summary` table.
- `plugins/sdd/agents/qa-engineer.md` is deleted.

#### Step 2

The plugins/sdd/agents/tech-lead.md and plugins/sdd/agents/team-lead.md doing complimentary work, one by one, but it increase planing time.

[] Merge tech-lead.md and team-lead.md into one agent -> tech-lead.md. He should perform ALL work that currently is done by tech-lead.md AND team-lead.md. So don't lose any steps in their workflows after combining them. It still should produce the steps as now and parallilaize them.
    [] CRITICAL: Avoid summaraising or decreasing the tech-lead OR team-lead prompt. You should copy where possible, and change only what need.
[] Remove team-lead.md and his mentions from plan-task workflow.
[] While merging, adjust tech-lead and team-lead processes:
    [] In task file, tech-lead now should write only Implementation Process section (Parallelization Overview, Phase Overview). The Implementation Strategy and Least-to-Most Decomposition Chain should no be only in scratchbook, remove them from final task file.
    [] Each step now should be written as separate subtask in `.specs/sub-tasks/<task-name>/<step-name>.md` file. So it can be read by agent that doing this step independently. But, in step template, add section that mention path to main task file, so agent can reference it. CRITICAL: keep same template for step, but now turn it into temaplte for subtask md file. (DO NOT LOSE ANY CONTENT FROM STEP TEMPLATE!)
    [] Update Phase Overview section in tech-lead template to this:
        ```md
        ### Phase Overview

        #### Phase 1

        Steps: `<step-1-name>`, `<step-2-name>`, ...
        Acceptance Criteria that should be fulfiled:
        Checklist items:
        - `<checklist-item-1>`
        - `<checklist-item-2>`
        - ...

        Rubrics:
        - `<rubric-1>`
        - `<rubric-2>`
        - ...

        #### Phase 2

        Steps: `<step-1-name>`, `<step-2-name>`, ...
        Acceptance Criteria that should be fulfiled:
        Checklist items:
        - `<checklist-item-1>`
        - `<checklist-item-2>`
        - ...
        ```
    [] The agent previusly was too much focusing on Top-Down/Bottom-Up/Mixed, while ignoring other ways to implement it. Give specfic instruction to find a proper way to implement task, that more align wit it. He can use Top-Down/Bottom-Up/Mixed approaches, or can use feature based approach, where each phase focused on own feature/functionality (for example textures, logic, audit, graphic) and as result all of them done in parallel by own sequeintial step list. Or he can invent own approach to implement task, that best suitable for it. Main goal stays the same, he must find a way to implement task in the most efficient way, while keeping enough granularity of steps (not too big, not too small). So he can in best way utilize each model limits and capabilities at each step (Opus, sonnet, haiku)
    [] The verification by code-reviewer no longer will be done after each step. Now it will be done at phase level. To save resources on reiteration. This is why teah-lead must place them carefully. While step is granular enough sub-task, the phase must be specfici, focused at own results/acceptance criteria target, milestone that ALLWAYD should have two things:
        - Working application/service/solution -> so it can be commited and tested manually, but may not yet produce all the results/acceptance criteria that task is expected to produce.
        - Have tests/other verification artifacts -> so it can be properly reviewed by code-reviewer according to Acceptance Criteria.
    Esentailly, it means that: while task can be considered as Pull Request, the each phase is commit in this pull request, that still should keep applicaiton working and and CI green. So each phase naturally grows on previus functionality, but still should be self-contained and verifiable.
    It is okay to keep a single phase for whole task with 5-10 steps, if there no way to make intermidiate verifiable checks, and whole solution will be working and test will be green only at the end of the task. Much worther to place in each phase a single step, which will result in verification iteration on each small change. But still, making phases too big (5-10 steps), will mean that reviewer will need to check too much code/tests and he may miss something, or if he will find something, the developer will need to reiterate on too much issues, that compaunded over time. Esentially rewriting whole phase from scratch.
    [] While each step still should have implementation model defined, the phase now also should have reviewer model defined by tech-lead. He should choose them appropriatly, but usally reviwer model should be one step higher than implementation model. For example such phases may be regular:
       - Phase reviwer Sonnet: Step 1: Haiku -> Step 2: Haiku -> Step 3: Haiku
       - Phase reviwer Opus: Step 1: Sonnet -> Step 2: Sonnet -> Step 3: Sonnet
       - Phase reviwer Sonnet: Step 1: Sonnet -> Step 2: Haiku -> Step 3: Sonnet
       - Phase reviwer Opus: Step 1: Sonnet -> Step 2: Haiku -> Step 3: Opus
    [] Add to tech-lead prompt example section, examples how he can define implementation strategy/phases: 
    - Top-Down Example
    - Bottom-Up Example
    - Mixed Example
    - Feature Based Example
    - Task specfic Example
    [] In parallization overview section, the tech-lead should add path for each sub-task file, so agent can reference it.

##### Step 2 — Design Decisions

- **Merged scratchpad flow** (copy-not-summarize): Problem Decomposition -> Sequential Solving -> Implementation Strategy Selection -> Task Breakdown Strategy -> draft Implementation Steps -> Dependency Analysis -> Parallel Opportunities -> Tightly Coupled Groups -> Dependency Graph -> Agent Assignments -> Restructured Steps -> one merged Self-Critique loop (tech-lead's 8 verification questions + team-lead's 6).
- **Sub-task file naming**: `.specs/sub-tasks/<task-name>/<NN>-<step-slug>.md` — numeric prefix makes execution order visible on disk and keeps names collision-free. `<task-name>` is the task filename without extension.
- **Sub-task folder never moves.** It is created at planning time and stays put while the task file travels `draft/` -> `todo/` -> `in-progress/` -> `done/`, so stored paths never go stale.
- **Sub-task template** = the current restructured step template with NOTHING removed (`**Model:**`, `**Agent:**`, `**Depends on:**`, `**Parallel with:**`, `**Note:**`, step description, `#### Expected Output`, `#### Success Criteria`, `#### Subtasks`) PLUS a new `**Task File:**` back-reference line pointing at the parent task file.
- **`create-folders.sh`** must create `.specs/sub-tasks/` with a `.gitkeep`. It is tracked in git, NOT added to the gitignore patterns (sub-tasks are spec artifacts, like task files).
- **Phase Overview** additionally carries a `Reviewer model:` line per phase, alongside `Steps:` and the checklist-items / rubrics lists from the user's template above. It carries NO threshold line.
- **Homeless tech-lead sections**: `## Implementation Summary`, `## Risks & Blockers Summary` and `## Definition of Done (Task Level)` leave the task file. Definition of Done now comes from the business-analyst's Acceptance Criteria section. Per-step risks and blockers move into the corresponding sub-task file; the task-level risk roll-up stays in the scratchpad.
- **Strategy selection is broadened**: Top-Down / Bottom-Up / Mixed become examples rather than the menu, and a new Examples section carries five worked examples (Top-Down, Bottom-Up, Mixed, Feature-Based, Task-Specific).
- `plugins/sdd/agents/team-lead.md` is deleted.

##### Step 2b — plan-task workflow rewrite (`plugins/sdd/skills/plan-task/SKILL.md`)

The pipeline drops from six model-assigned phases to four:

```
2a research        ─┐
2b codebase analysis├─→ 3 architecture synthesis ─→ 4 decomposition ─→ promote draft/ → todo/
2c business analysis┘   [sdd:software-architect]     [sdd:tech-lead]
```

- Stage names reduce to `research`, `codebase analysis`, `business analysis`, `architecture synthesis`, `decomposition`. `parallelize` and `verifications` are removed.
- **One judge per phase, folded rubrics, weights renormalized to 1.0, max ~7 dimensions:**
  - **Judge 2c** = Description Clarity, Criteria Quality, Scenario Coverage, Scope Definition + (from old Judge 6) Rubric Quality, Coverage Completeness, Test Strategy Coverage. Old Judge 6's *Verification Level Appropriateness* and *Threshold Appropriateness* are dropped — both concepts are deleted by Step 1 / Step 3.
  - **Judge 4** = Step Quality, Success Criteria Testability, Risk Coverage, Completeness + (from old Judge 5) Dependency Accuracy, Parallelization Maximized, Agent/Model Selection Correctness + a new **Phase Design** criterion (does each phase leave a working, independently verifiable milestone, and is its reviewer model appropriate?) and sub-task file completeness. Overlapping criteria are merged rather than dropped (e.g. *Execution Directive Present* folds into Completeness).
- Phase 4's launch prompt inherits what previously went to Phase 5: the available-agents list and the per-step Model Selection Policy table.
- **Cross-reference sweep** (per `.claude/rules/refactor-cross-references.md`): `--fast` alias stage list, `--one-shot` alias, `--refine` Section-to-Stage mapping, TodoWrite initialization list, Complete Workflow Overview diagram, Phase Weighting table, Quality Gates Summary table, Artifacts Generated tree (gains `.specs/sub-tasks/`), and the completion table's *Parallelization Depth* / *Total Verifications* rows.
- Verification: `grep -nE "qa-engineer|team-lead|Phase 5|Phase 6|parallelize|verifications"` over the file returns zero hits.

#### Step 3

Update plugins/sdd/skills/implement-task workflow to new specifics of planning workflow:
[] The orcestrator now should provide to immplementation agent path to task file AND sub-task file which he must implement.
[] The orcestrator now should call code-reviewer only at the end of each phase, with model that was provided in phase overview. But if reviewer have found issues, he have freedom to decide which model should be used to fix them, and which one should review the fixes. It is most critical job of the implementation orcestrator, so he must think throughfully. For example, if whole phase was done by multiple haiku agents, but was fully failed, he can launch fix by sonnet or opus agent, instead of haiku. But if only single step from all was failed, and not involve rewriting the rest, he can launch haiku agent to fix only this part.

##### Step 3 — Design Decisions

**`plugins/sdd/agents/code-reviewer.md` — rewrite the input contract from step-level to phase-level:**

- Inputs become: task file path, phase identifier, the artifact paths reported by the developers, and `CLAUDE_PLUGIN_ROOT`. The reviewer **resolves the phase's sub-task file paths itself** from the task file (Phase Overview + Parallelization Overview) — they are not passed in.
- It MUST read the phase block in the task file AND all sub-task files of that phase, to understand the expected end state of the phase.
- Stage 4 reads `## Acceptance Criteria` (checklist / regular checks / rubric / score definitions / test strategy) and scores **only** the checklist items and rubrics that this phase's Phase Overview lists.
- **CRITICAL — partial fulfilment**: a phase is a checkpoint, not the finish line. Acceptance criteria NOT listed for this phase are not yet due, and the reviewer MUST NOT score them as missing, unimplemented, or incomplete.
- Frontmatter `description`, Identity, Goal and Input sections are updated from "per-step" to "per-phase" wording.
- Stage 4 fallback rules are re-anchored to the new section names; the dead `per qa-engineer §5.7` reference (line ~654) points at the merged business-analyst instead.

**`plugins/sdd/skills/implement-task/SKILL.md`:**

- Developers are dispatched per step with the task file path AND their sub-task file path, at the model named in the sub-task file.
- One `sdd:code-reviewer` runs at the END of each phase, at that phase's `Reviewer model`. Patterns A / B / B-Panel / C collapse into a single phase-review pattern; the Panel Voting Algorithm section is removed with them.
- **Config**: a single `THRESHOLD`, default **4.0**. `THRESHOLD_FOR_CRITICAL_COMPONENTS` / `THRESHOLD_FOR_STANDARD_COMPONENTS` and the two-value `--target-quality X.X,Y.Y` parsing are deleted. `--lenient-threshold` is deleted (it keyed off a qa-engineer "lenient" marking that no longer exists). No thresholds are read from the task file.
- `--human-in-the-loop` switches from step numbers to phase identifiers; `--continue` / `--refine` resolve state by phase + step.
- **Failure handling is stated as a principle, not a rule table.** The orchestrator must reason about the blast radius of the reviewer's findings before choosing the fix model and the re-review model — this is its most critical judgement. The user's case is given as one worked example (a whole phase built by haiku agents that failed entirely may warrant a sonnet/opus fix; a single isolated failed step that does not require rewriting the rest may warrant a haiku fix), and other situations are derived from that principle rather than enumerated.
- Phase 3's Definition-of-Done verification survives unchanged, now reading Definition of Done from the Acceptance Criteria section.

#### Step 4

Update documentation to match the new workflow.

[] Update every file that references the removed agents or the old workflow shape:
  - `plugins/sdd/README.md` — agent roster (10 -> 8), four-phase planning pipeline, sub-task file layout
  - `README.md` (root) — SDD agent listing
  - `docs/reference/agents.md` — delete `qa-engineer` and `team-lead` entries; rewrite `business-analyst`, `tech-lead` and `code-reviewer` descriptions
  - `docs/plugins/sdd/plan-task.md` — stage table, flags, judges, phase diagram
  - `docs/plugins/sdd/implement-task.md` — phase-level review, dispatch patterns, threshold flags
  - `docs/plugins/sdd/README.md` — Key Features
  - `docs/plugins/sdd/usage-examples.md` — examples referencing removed stages/flags
  - `docs/guides/spec-driven-development.md` — workflow narrative
  - Anywhere the `.specs/` tree is drawn: add `.specs/sub-tasks/`
[] Sync direction is `just sync-plugins-to-docs` (plugin README is the source). Do NOT hand-edit both copies.
[] Bump versions with `just` only, never by hand: `just set-version sdd 3.5.0` (minor), then `just set-marketplace-version <next>`.
[] Verify `.claude-plugin/marketplace.json` needs no agent-list edit (`plugins/sdd/.claude-plugin/plugin.json` holds no agents/skills arrays).

##### Task-level completion checks

- `grep -rn "qa-engineer\|team-lead" plugins/ docs/ README.md` returns zero hits.
- No file still describes `#### Verification` sections, verification levels (None / Single Judge / Panel of 2 / Per-Item), panel voting, or the `parallelize` / `verifications` stages.

