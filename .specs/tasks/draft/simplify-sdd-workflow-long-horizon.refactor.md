---
title: Simplify SDD workflow for long horizon tasks
---

## Requirements

simplify plugins/sdd/skills/plan-task workflow for long horizon tasks


### Step 1

The plugins/sdd/agents/qa-engineer.md and plugins/sdd/agents/business-analyst.md doing esentially the same work now, but at different stages. This makes plan-task workflow is too long. But they also have some parts that other not doing, so their work not dublication, rather different angle of view.

[] Merge the qa-engineer.md and business-analyst.md into one agent -> business-analyst.md. He should perform ALL work that currently is done by qa-engineer.md AND business-analyst.md. So don't lose any steps in their workflows after combining them. It still should produce the Description as now, but acceptance criteria should be different. Agent firstly should write them in scratchbook, as it doing now. But then it should go through QA engineer processes Context Analysis -> Per-Step Checklist -> Per-Step Principles -> ... . Final results should contain. What is currently wrote in Verification section by QA Engineer (Checklist, Rubric, etc.), but in Acceptance Criteria section. The verificaition section no longer needed. 
[] CRITICAL: Acceptance Criteria from business perspective still should be written, but now only in scratchbook. Final Acceptance Criteria (checklist, rubric, etc.) should contain technical AND business criteria mixed in a way that most appropriate to define verification of task. And test apporach (Tes Strategy, Test Matrix, etc) should present there.
[] CRITICAL: Avoid summaraising or decreasing the business analytst OR QA engineer prompt. You shuold copy where possible, and change only what need.
[] While merging, adjust QA engineer process:
  [] It not longer should be done per-step, as it was before. Steps now written later in workflow, so Business Analyst (previously QA Engineer) should now focus on WHOLE task verification, rather then specific steps.
  [] Decrease QA Engineer process artifacts focus. It can still mention in his acceptance criteria artifacts, if they mentioned in user prompt, but it no longer the focus. Artifacts code/test fails can be defined by solution architect later in workflow. So QA Engineer may not know about them. Instead he must focus more on overral feature and functionality verification + test approach: Define testing strategy (unit, integration, etc), test matrix, test cases to cover, by which types of tests. So overral verification of tests can be done across all tests types at the end, no metter where they are written.
[] Remove qa-engineer.md and his mentions from plan-task workflow.

### Step 2

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

### Step 3

Update plugins/sdd/skills/implement-task workflow to new specifics of planning workflow:
[] The orcestrator now should provide to immplementation agent path to task file AND sub-task file which he must implement.
[] The orcestrator now should call code-reviewer only at the end of each phase, with model that was provided in phase overview. But if reviewer have found issues, he have freedom to decide which model should be used to fix them, and which one should review the fixes. It is most critical job of the implementation orcestrator, so he must think throughfully. For example, if whole phase was done by multiple haiku agents, but was fully failed, he can launch fix by sonnet or opus agent, instead of haiku. But if only single step from all was failed, and not involve rewriting the rest, he can launch haiku agent to fix only this part.

