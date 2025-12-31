---
description: Add LLM-as-Judge verification sections to task implementation steps
argument-hint: Task ID (e.g., cek-31ce) with implementation steps defined
---

# Define Task Verifications Command

<task>
You are a verification specialist. Analyze implementation steps in minibeads tasks and add appropriate LLM-as-Judge verification sections with rubrics, thresholds, and execution patterns.
</task>

<context>
This command adds verification sections to task implementation steps by:

1. Analyzing each step's artifact type and criticality
2. Determining appropriate verification level (None, Single, Panel, Per-Item)
3. Defining custom rubrics with weighted criteria
4. Specifying thresholds and reference patterns
5. Adding `#### Verification` sections to each step
</context>

<workflow>

## Phase 1: Load and Understand Task

1. **Read the task file** to get full implementation process:

   ```bash
   Read .beads/issues/$TASK_ID.md
   ```

2. **Identify all implementation steps**:
   - Locate `## Implementation Process` section
   - List all steps with their Expected Output and Success Criteria
   - Note artifact types being created/modified

## Phase 2: Classify Each Step

For each step, determine:

1. **Artifact Type** (examples by category):

   **Code & Logic:**
   - Source code (functions, classes, modules)
   - API endpoints / controllers
   - Business logic / domain services
   - Data models / schemas
   - Algorithms / core utilities

   **Infrastructure & Config:**
   - Configuration files (JSON, YAML, env)
   - Build scripts / CI/CD pipelines
   - Database migrations / schemas
   - Deployment manifests (Docker, K8s)

   **Tests & Quality:**
   - Unit tests
   - Integration tests
   - E2E tests
   - Test fixtures / mocks

   **Documentation & Prompts:**
   - API documentation
   - README files
   - User guides
   - Agent definitions / prompts
   - Workflow commands / task files

   **Simple Operations:**
   - Directory creation
   - File renaming / moving
   - File deletion
   - Simple refactoring (rename variables)

2. **Criticality Level**:

   Assess based on **impact of defects**, not artifact type alone:

   | Criticality | Impact if Defective | Examples |
   |-------------|---------------------|----------|
   | **HIGH** | Security vulnerabilities, data loss, system failures, hard-to-debug issues | Auth logic, payment processing, data migrations, core algorithms, API contracts, agent definitions |
   | **MEDIUM-HIGH** | Broken functionality, poor UX, test failures catch issues | Business logic, UI components, integration code, workflow orchestration, task files |
   | **MEDIUM** | Degraded quality, user confusion, maintainability issues | Documentation, utility functions, helper code, configuration |
   | **LOW** | Minimal impact, easily caught/fixed | Formatting, comments, non-critical config, logging |
   | **NONE** | Binary success/failure, no judgment needed | Directory creation, file deletion, file moves |

   **Criticality Factors to Consider:**
   - Does it handle user data or authentication?
   - Can bugs cause data loss or corruption?
   - Is it a public API or interface contract?
   - How hard is it to detect and debug issues?
   - What's the blast radius if it fails?

3. **Item Count**:
   - Single item → Single Judge or Panel
   - Multiple similar items → Per-Item Judges

## Phase 3: Determine Verification Level

Use this decision tree:

```
Is artifact type Directory/Deletion/Config?
├── Yes → Level: NONE
│
└── No → Is criticality HIGH?
    ├── Yes → Level: Panel of 2 Judges
    │
    └── No → Are there multiple similar items?
        ├── Yes → Level: Per-Item Judges (one per item)
        │
        └── No → Level: Single Judge
```

### Verification Levels

| Level | When to Use | Configuration |
|-------|-------------|---------------|
| ❌ None | Simple operations (mkdir, delete, JSON update) | Skip verification |
| ✅ Single Judge | Non-critical single artifacts | 1 evaluation, threshold 4.0/5.0 |
| ✅ Panel (2) | Critical single artifacts | 2 evaluations, median voting, threshold 4.0/5.0 |
| ✅ Per-Item | Multiple similar items | 1 evaluation per item, parallel, threshold 4.0/5.0 |

## Phase 4: Define Rubrics

For each step requiring verification, create a rubric with:

1. **3-6 criteria** relevant to the artifact type
2. **Weights summing to 1.0**
3. **Clear descriptions** of what each criterion measures

### Rubric Templates by Artifact Type

#### Source Code / Business Logic Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Correctness | 0.30 | Implements requirements correctly |
| Code Quality | 0.20 | Follows project conventions, readable |
| Error Handling | 0.20 | Handles edge cases, failures gracefully |
| Security | 0.15 | No vulnerabilities, proper validation |
| Performance | 0.15 | No obvious inefficiencies |

#### API / Interface Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Contract Correctness | 0.25 | Request/response match specification |
| Error Responses | 0.20 | Proper error codes, messages |
| Validation | 0.20 | Input validation complete |
| Documentation | 0.15 | Endpoints documented correctly |
| Consistency | 0.20 | Follows existing API patterns |

#### Test Code Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Coverage | 0.25 | Tests cover requirements |
| Edge Cases | 0.25 | Edge cases and error paths tested |
| Isolation | 0.20 | Tests are independent, no side effects |
| Clarity | 0.15 | Test intent is clear from name/structure |
| Maintainability | 0.15 | Tests are not brittle |

#### Database / Schema Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Data Integrity | 0.30 | Constraints preserve data integrity |
| Migration Safety | 0.25 | Reversible, no data loss |
| Performance | 0.20 | Indexes, efficient queries |
| Naming | 0.15 | Follows naming conventions |
| Documentation | 0.10 | Schema changes documented |

#### Configuration Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Correctness | 0.35 | Values are correct for environment |
| Security | 0.25 | No secrets exposed, proper permissions |
| Completeness | 0.20 | All required fields present |
| Consistency | 0.20 | Follows project config patterns |

#### Documentation Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Accuracy | 0.30 | Content is factually correct |
| Completeness | 0.25 | All necessary information included |
| Clarity | 0.20 | Easy to understand |
| Examples | 0.15 | Helpful examples where needed |
| Consistency | 0.10 | Terminology matches codebase |

#### Refactoring Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Behavior Preserved | 0.35 | No functional changes (unless intended) |
| Code Quality Improved | 0.25 | Measurably better than before |
| Tests Pass | 0.20 | All existing tests still pass |
| No Regressions | 0.20 | No new issues introduced |

---

### Claude Code Specific Rubrics

#### Agent Definition Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Pattern Conformance | 0.25 | Follows existing agent patterns (frontmatter, structure) |
| Frontmatter Completeness | 0.20 | Has name, description, tools fields |
| Domain Knowledge | 0.25 | Demonstrates domain-specific expertise |
| Documentation Quality | 0.15 | Clear role, process, output format sections |
| RFC 2119 Bindings | 0.15 | Uses MUST/SHOULD/MAY appropriately |

#### Workflow Command Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Orchestrator Leanness | 0.20 | ~50-100 tokens per step dispatch |
| Task Path References | 0.15 | Uses ${CLAUDE_PLUGIN_ROOT}/tasks/ correctly |
| Step Responsibility | 0.25 | Clear main agent vs sub-agent split |
| User Interaction | 0.15 | Appropriate interaction points |
| Parallel Execution | 0.15 | Optimal parallelization |
| Completion Flow | 0.10 | Summary and next steps present |

#### Task File Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Self-Containment | 0.25 | Sub-agent doesn't need external context |
| Context Section | 0.15 | Clear workflow position |
| Goal Clarity | 0.20 | Specific, measurable goal |
| Instructions Quality | 0.20 | Numbered, actionable steps |
| Success Criteria | 0.15 | Checkboxes with measurable outcomes |
| Input/Output Contract | 0.05 | Clear contracts defined |

---

### Documentation Specific Rubrics

#### Documentation Rubric (README)

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Structure Completeness | 0.25 | All required sections present |
| Content Accuracy | 0.20 | Commands/agents documented correctly |
| Sync Accuracy | 0.15 | Matches related docs (if synced) |
| Usage Examples | 0.15 | Helpful examples included |
| Consistency | 0.15 | Terminology consistent |
| Integration Quality | 0.10 | Fits naturally with existing content |

#### Documentation Rubric (Other Docs)

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Reference Added | 0.30 | New feature/plugin mentioned appropriately |
| Consistency | 0.25 | Terminology matches source README |
| Integration Quality | 0.25 | Fits naturally with existing content |
| No Redundancy | 0.20 | Complements without duplicating |

### Custom Rubric Guidelines

When creating custom rubrics:

1. **Extract criteria from Success Criteria** - Task's own success criteria often map to rubric criteria
2. **Weight by importance** - Critical aspects get 0.20-0.30, minor aspects get 0.05-0.15
3. **Be specific** - "Documents hypothesis file format" not "Good documentation"
4. **Match artifact type** - Code artifacts need different criteria than documentation

## Phase 5: Add Verification Sections

For each step, add `#### Verification` section after `#### Success Criteria`:

### Template: No Verification

```markdown
#### Verification

**Level:** ❌ NOT NEEDED
**Rationale:** [Why verification is unnecessary - e.g., "Simple file operation. Success is binary."]
```

### Template: Single Judge

```markdown
#### Verification

**Level:** ✅ Single Judge
**Artifact:** `[path/to/artifact.md]`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| [Criterion 1] | 0.XX | [Description] |
| [Criterion 2] | 0.XX | [Description] |
| ... | ... | ... |

**Reference Pattern:** `[path/to/reference.md]` (if applicable)
```

### Template: Panel of 2 Judges

```markdown
#### Verification

**Level:** ✅ CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `[path/to/artifact.md]`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| [Criterion 1] | 0.XX | [Description] |
| [Criterion 2] | 0.XX | [Description] |
| ... | ... | ... |

**Reference Pattern:** `[path/to/reference.md]`
```

### Template: Per-Item Judges

```markdown
#### Verification

**Level:** ✅ Per-[Item Type] Judges ([N] separate evaluations in parallel)
**Artifacts:** `[path/to/items/{item1,item2,...}.md]`
**Threshold:** 4.0/5.0

**Rubric (per [item type]):**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| [Criterion 1] | 0.XX | [Description] |
| [Criterion 2] | 0.XX | [Description] |
| ... | ... | ... |

**Reference Pattern:** `[path/to/reference.md]` (if applicable)
```

## Phase 6: Add Verification Summary

After all steps, add a summary table before `## Blockers`:

```markdown
---

## Verification Summary

| Step | Verification Level | Judges | Threshold | Artifacts |
|------|-------------------|--------|-----------|-----------|
| 1 | ❌ None | - | - | [Brief description] |
| 2a | ✅ Panel (2) | 2 | 4.0/5.0 | [Brief description] |
| 2b | ✅ Per-Item | N | 4.0/5.0 | [Brief description] |
| ... | ... | ... | ... | ... |

**Total Evaluations:** [Calculate total]
**Implementation Command:** `/implement-task $TASK_ID`

---
```

## Phase 7: Update Task File

**Use Write tool to modify the task file directly**:

1. **Preserve everything before first step**
2. **Add `#### Verification` section to each step** (after Success Criteria)
3. **Add Verification Summary** before Blockers section
4. **Preserve Blockers and Notes sections**

</workflow>

<verification_principles>

## Key Principles

### 1. Match Verification to Risk

Higher risk artifacts need more thorough verification:

- **HIGH criticality** (auth, payments, data, core logic) → Panel of 2 Judges
- **MEDIUM-HIGH** (business logic, integrations) → Single Judge or Panel
- **MEDIUM** (docs, utilities, helpers) → Single Judge or Per-Item
- **LOW** (formatting, comments) → Single Judge with lower threshold
- **NONE** (file operations, schema-validated) → Skip verification

### 2. Custom Rubrics Over Generic

Extract rubric criteria from the step's own Success Criteria when possible. This ensures the rubric measures what the task actually requires.

### 3. Reference Patterns Enable Quality

Always specify a reference pattern when one exists. Judges use these to calibrate expectations.

### 4. Threshold Selection

| Threshold | When to Use |
|-----------|-------------|
| 4.0/5.0 | Standard - most artifacts |
| 4.5/5.0 | High stakes - security, core functionality |
| 3.5/5.0 | Lenient - first drafts, experimental |

### 5. Per-Item vs Panel

- **Per-Item**: Multiple similar items (task files, doc updates)
- **Panel**: Single critical item needing multiple perspectives

</verification_principles>

<checklist>

Before completing verification definition:

- [ ] **Every step has `#### Verification` section**
- [ ] **Verification level matches artifact criticality**
- [ ] **Rubric weights sum to 1.0** for each rubric
- [ ] **Rubric criteria are specific** (not generic)
- [ ] **Reference patterns specified** where applicable
- [ ] **Per-Item count matches actual items**
- [ ] **Verification Summary table added**
- [ ] **Total evaluations calculated**

</checklist>

<example_session>

### Example 1: Software Development Task

User: /define-task-verifications cek-abc1

**Phase 1: Loading task...**

Task: "Add user authentication to the API"

**Phase 2: Classifying steps...**

| Step | Artifact Type | Criticality | Items |
|------|---------------|-------------|-------|
| 1 | Database migration | HIGH | 1 |
| 2 | User model | HIGH | 1 |
| 3 | Auth service | HIGH | 1 |
| 4 | API endpoints | HIGH | 3 |
| 5 | Unit tests | MEDIUM-HIGH | 4 |
| 6 | Integration tests | MEDIUM-HIGH | 2 |
| 7 | API documentation | MEDIUM | 1 |
| 8 | Config updates | LOW | 1 |

**Phase 3: Determining verification levels...**

| Step | Level | Rationale |
|------|-------|-----------|
| 1 | Panel (2) | Data integrity, hard to undo |
| 2 | Panel (2) | Core data model, affects many systems |
| 3 | Panel (2) | Security-critical, auth logic |
| 4 | Per-Item (3) | Multiple endpoints, each needs security review |
| 5 | Per-Item (4) | Multiple test files |
| 6 | Single | Integration tests, fewer items |
| 7 | Single | Documentation, medium priority |
| 8 | None | Simple config, schema-validated |

**Phase 4: Defining rubrics...**

Step 3 rubric (Auth Service - using Source Code rubric with security emphasis):

- Correctness (0.25): Implements auth flow correctly
- Security (0.30): No vulnerabilities, proper hashing, token handling
- Error Handling (0.20): Handles invalid credentials, expired tokens
- Code Quality (0.15): Follows project patterns
- Performance (0.10): Efficient token validation

**Total Evaluations:** 16

---

### Example 2: Claude Code Plugin Task

User: /define-task-verifications cek-31ce

**Phase 1: Loading task...**

Task: "Reorganize FPF plugin using workflow command pattern"

**Phase 2: Classifying steps...**

| Step | Artifact Type | Criticality | Items |
|------|---------------|-------------|-------|
| 1 | Directory creation | NONE | 2 dirs |
| 2a | Agent definition | HIGH | 1 |
| 2b | Workflow command | HIGH | 1 |
| 3 | Utility commands | MEDIUM | 5 |
| 4 | Task files | MEDIUM-HIGH | 7 |
| 5 | Configuration (JSON) | LOW | 1 |
| 6a | Documentation (README) | MEDIUM | 2 |
| 6b | Documentation (other) | MEDIUM | 6 |
| 7 | File deletion | NONE | 7 |

**Phase 3: Determining verification levels...**

| Step | Level | Rationale |
|------|-------|-----------|
| 1 | None | Directory creation, binary success |
| 2a | Panel (2) | High criticality, controls agent behavior |
| 2b | Panel (2) | High criticality, orchestration logic |
| 3 | Per-Item (5) | Medium criticality, multiple items |
| 4 | Per-Item (7) | Medium-high, sub-agent instructions |
| 5 | None | JSON schema validation sufficient |
| 6a | Panel (2) | User-facing README, quality matters |
| 6b | Per-Item (6) | Multiple docs, each needs review |
| 7 | None | File deletion, binary success |

**Phase 4: Defining rubrics...**

Step 2a rubric (Agent Definition):

- Pattern Conformance (0.25): Follows plugins/sdd/agents/software-architect.md pattern
- Frontmatter Completeness (0.20): Has name, description, tools fields
- FPF Domain Knowledge (0.25): Demonstrates L0/L1/L2 layer understanding
- Hypothesis File Format (0.15): Documents hypothesis file format clearly
- RFC 2119 Bindings (0.15): Uses MUST/SHOULD/MAY for file operations

**Total Evaluations:** 24

</example_session>

<output>
After defining verifications, report:

1. **Task Updated**: $TASK_ID
2. **Steps with Verification**: X of Y steps
3. **Verification Breakdown**:
   - Panel (2 evaluations): X steps
   - Per-Item evaluations: X steps (Y total evaluations)
   - No verification: X steps
4. **Total Evaluations**: X

Suggest:

- `mb show $TASK_ID` to review the task
- `/implement-task $TASK_ID` to execute with verification
</output>
