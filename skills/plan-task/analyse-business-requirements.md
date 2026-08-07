# Analyse Business Requirements

## Goal

Your goal is to refine the task description and create comprehensive acceptance criteria that enable developers to understand exactly what needs to be built and how success will be measured. Use a **scratchpad-first approach**: gather ALL analysis in a scratchpad file, then selectively copy only verified, relevant findings into the task file.

**CRITICAL**: Vague requirements cause implementation failures. Untestable criteria waste developer time. Incomplete scope leads to endless rework. YOU are responsible for specification quality. There are NO EXCUSES for delivering incomplete, vague, or untestable requirements.

## Input

- **Task File**: Path to the task file (e.g., `.specs/tasks/task-{name}.md`)

## Business Analysis Process

### STAGE 1: Setup Scratchpad

**MANDATORY**: Before ANY analysis, create a scratchpad file for your business analysis thinking.

1. Run the scratchpad creation script `bash ${CLAUDE_PLUGIN_ROOT}/scripts/create-scratchpad.sh` - it will create the file: `.specs/scratchpad/<hex-id>.md`
2. Use this file for ALL your discoveries, analysis, and draft sections
3. The scratchpad is your workspace - dump EVERYTHING there first

```markdown
# Business Analysis Scratchpad: [Task Title]

Task: [task file path]
Created: [date]

---

## Phase 1: Requirements Discovery

[Stage 2 content...]

## Phase 2: Concept Extraction

[Stage 3 findings...]

## Phase 3: Requirements Analysis

[Stage 4 analysis...]

## Phase 4: Draft Output

[Stage 5 synthesis...]

## Self-Critique

[Stage 7 verification...]
```

---

### STAGE 2: Requirements Discovery

YOU MUST elicit the true business need behind the request. Probe beyond surface-level descriptions to uncover underlying problems, stakeholder motivations, and success criteria. NEVER accept the first description at face value.

#### Template for Your Analysis

Use this template to write in scratchpad file:

```markdown
## Phase 1: Requirements Discovery

### Task Overview
- Initial User Prompt: [quote from task file]
- Current Description: [existing description if any]
- Task Type: [task/bug/feature]
- Complexity: [S/M/L/XL]

### Problem Definition (Step-by-Step Analysis)

Let's think step by step about what the user actually needs...

Step 1: What is the surface-level user request?
[Your analysis]

Step 2: What is the user actually trying to accomplish?
[Your analysis]

Step 3: What is the business value?
[Your analysis]

Step 4: Who benefits from this change and how?
[Your analysis]

Step 5: What features of this solution may be added imidiatly or in future?
[Your analysis]

Step 6: What constraints or considerations exist?
[Your analysis]

Therefore, the root problem is: [Your conclusion]

### Scope
- What is included in this task?
- What is explicitly NOT included?
- What are the boundaries?

### Ambiguous Areas
- [List unclear aspects that need resolution]
```

If input is empty: Stop and report ERROR: "No task description provided"

#### Examples of Problem Definition Step-by-Step Analysis

Example 1: E-commerce Feature Request:

**User Request**: "Add a wishlist feature to the product pages"

Let's think step by step about what the user actually needs...

Step 1: What is the surface-level request?
The user wants a wishlist feature on product pages. This seems straightforward - a button to save products for later.

Step 2: Why would users need a wishlist?
Users browse products but aren't ready to buy immediately. They might be: comparing options, waiting for a sale, saving gift ideas, or budgeting for future purchases. The wishlist solves the problem of "I found something I like but can't act on it now." In simular way user may also want to save products for comparison with other products. Additionally, user may want to have multiple wishlists for different purposes: future purchases, gifts, etc.

Step 3: What is the business value?
It not directly allow to increase conversion rate, but it allows to increase customer engagement and retention. Also it allows to know in what products user is interested in and what products are not. As a result it can be used for targeted marketing and sales.

Step 4: What features of this solution may be added imidiatly or in future?

- Add a button to save products for later
  - Which can show select with different lists: future purchases, gifts, etc.
- Add a button to save products for comparison
- Page to see all wishlists and products in them
  - Functionality to create new list
  - Functionality to delete item
  - Functionality to rename list
  - Functionality to share list
  - Functionality to delete list
- Page to see product comparision
- Functionality to subscribe for product or whole list if it will be on sale

Step 5: What constraints or considerations exist?

- Should it wor across devices (users browse on mobile, buy on desktop)
- Should lists to be thinkied between devices?
- Privacy: wishlist data not critical, untill it not allow to track exact user identity
- Guest users: Do they get wishlists? Requires account?

Therefore, the root problem is: "Users who discover products they want but aren't ready to purchase have no way to maintain that interest, leading to lost conversions." The wishlist, comparison and subscription features are a solution to this engagement retention problem.

**Example 2: Bug Report Analysis**:

**User Request**: "Fix the login timeout - users are complaining"

Let's think step by step about what the user actually needs...

Step 1: What is the reported problem?
Users are experiencing timeouts during login. This is a symptom, not necessarily the root cause.

Step 2: What could cause login timeouts?
Multiple possibilities: server response too slow, session configuration too aggressive, network latency issues, authentication service bottleneck, or database connection pool exhaustion. The "fix" depends entirely on the root cause.

Step 3: What is the actual user pain?
Users are frustrated because they can't access the system. But why? Are they losing work? Missing deadlines? The impact determines priority and acceptable solutions.

Step 4: What does "fix" mean in this context?
Could mean: eliminate timeouts entirely, extend timeout duration, provide better error messages, add retry logic, or improve login performance. Each is a different scope.

Step 5: What information is missing?

- How long is the current timeout? What's acceptable?
- How many users affected? All or specific conditions?
- When did this start? Recent change?
- What error do users see?

Therefore, the root problem requires investigation: "Users cannot reliably access the system due to login failures, causing [specific business impact]. The underlying cause and appropriate fix are not yet determined." This is a bug requiring diagnosis, not a simple feature implementation.

---

### STAGE 3: Concept Extraction (in scratchpad)

#### Template for Your Analysis

Use this template to write in scratchpad file:

```markdown
## Phase 2: Concept Extraction

### Key Concepts Identified

Let's think step by step about the core elements of this feature...

Step 1: Who are the actors?
[Your analysis]

Step 2: What actions/behaviors are involved?
[Your analysis]

Step 3: What data entities exist?
[Your analysis]

Step 4: What constraints apply?
[Your analysis]

Step 5: What's implicitly assumed?
[Your analysis]

Therefore, the key concepts are: [Summary]

### Concept Summary
- **Actors**: [Who interacts with this feature?]
- **Actions/Behaviors**: [What does the system do?]
- **Data Entities**: [What data is involved?]
- **Constraints**: [What limitations exist?]

### Implicit Assumptions
- [What is assumed but not stated?]

### Scope Analysis
- **In Scope**: [What's included]
- **Out of Scope**: [What's explicitly excluded]
- **Boundary Cases**: [Edge cases to consider]
```

#### Example of Concept Extraction Step-by-Step Analysis

**Example: Payment Processing Feature**:

**Requirement**: "Allow users to pay with multiple payment methods"

Let's think step by step about the core elements...

Step 1: Who are the actors?

- End users (customers making purchases)
- Payment processors (Stripe, PayPal, etc.)
- Finance team (reconciliation, refunds)
- System administrators (configuration)

Step 2: What actions/behaviors are involved?

- Select payment method at checkout
- Enter payment details
- Process payment authorization
- Handle payment success/failure
- Store payment method for future use (optional)
- Process refunds

Step 3: What data entities exist?

- PaymentMethod (type, last4, expiry, default flag)
- Transaction (amount, status, timestamp, reference)
- User (linked payment methods)
- Order (linked transaction)

Step 4: What constraints apply?

- PCI compliance for card data handling
- Regional restrictions (some methods not available everywhere)
- Currency limitations per payment method
- Transaction limits

Step 5: What's implicitly assumed?

- Users have valid payment sources
- Payment processors are available and configured
- Currency conversion is handled (or not?)
- Tax calculation happens before payment

Therefore, the key concepts are: multi-actor payment flow with strict compliance constraints, requiring integration with external processors and careful handling of sensitive financial data.

---

### STAGE 4: Requirements Analysis (in scratchpad)

YOU MUST define functional and non-functional requirements with absolute precision. Vague requirements are WORTHLESS. Establish clear acceptance criteria, success metrics, constraints, and assumptions. Structure requirements hierarchically from high-level goals to specific features.

#### Template for Your Analysis

Use this template to write in scratchpad file:

**4.1: User Scenarios**

```markdown
## Phase 3: Requirements Analysis

### Functional Requirements Analysis

Let's think step by step about the each requirement systematically...

[Follow the 5-step pattern demonstrated below]

### Functional Requirements
- [Requirement 1 - specific and testable]
- [Requirement 2 - specific and testable]
...

### Non-Functional Requirements
- [Requirement 1 - with measurable target]
- [Requirement 2 - with measurable target]
...

### Constraints & Assumptions
- [Constraint 1]
- [Constraint 2]
...

### Measurable Outcomes
- How will we know this is complete?
- What can be tested?
- What are the success metrics?

### User Scenarios

#### Primary Flow (Happy Path)
1. [Step 1]
2. [Step 2]
...

#### Alternative Flows
- [Scenario A]: [Steps]
- [Scenario B]: [Steps]

#### Error Scenarios
- [Error case 1]: [Expected behavior]
- [Error case 2]: [Expected behavior]
```

**Examples of Requirements Analysis Step-by-Step Analysis**:

**Example: File Upload Feature**:

**Requirement**: "Users should be able to upload documents"

Let's think step by step about making this testable...

Step 1: What does "upload documents" actually mean?
Need to define: what file types, what size limits, where files go, who can upload, what happens after upload. "Documents" is vague - PDFs? Word docs? Images? All of these?

Step 2: What is the happy path?
User selects file → System validates file → System uploads file → System confirms success → File is accessible. Each step needs specific criteria.

Step 3: What are the failure modes?

- File too large: What's the limit? What error message?
- Wrong file type: Which types allowed? How communicated?
- Upload interrupted: Resume? Retry? Data loss?
- Storage full: How handled?
- Duplicate file: Overwrite? Rename? Reject?

Step 4: How do we make each criterion testable?
BAD: "Upload should be fast" - How fast? Under what conditions?
GOOD: "Upload of a 10MB file completes within 30 seconds on standard broadband connection"

BAD: "Support common document types" - Which ones?
GOOD: "System accepts PDF, DOCX, XLSX, and PNG files"

Step 5: What non-functional requirements apply?

- Performance: Upload time relative to file size
- Security: Virus scanning, file type validation (not just extension)
- Reliability: No partial uploads left in storage
- Usability: Progress indicator, clear error messages

Therefore, the acceptance criteria must specify: allowed file types (PDF, DOCX, XLSX, PNG), size limit (50MB), upload time target (< 30s for 10MB), error messages for each failure mode, and storage/retrieval confirmation.

**Example: Search Functionality**:

**Requirement**: "Add search to find orders quickly"

Let's think step by step about making this testable...

Step 1: What does "quickly" mean in measurable terms?
"Quickly" is subjective. Need to define: results appear within X seconds, search covers Y fields, returns top Z results. Current pain point might give context - if users currently take 2 minutes to find orders, "quickly" means under 10 seconds.

Step 2: What should be searchable?
Order ID (exact match), customer name (partial match), product name, date range, status, amount range? Each searchable field has different matching logic.

Step 3: What results should appear?
List of matching orders with: order ID, date, customer, total, status. Sorted by relevance? Date? How is relevance defined?

Step 4: What are the edge cases?

- No results found: What message? Suggestions?
- Too many results: Pagination? Filter refinement prompt?
- Special characters in search: Escaped? Literal?
- Empty search: Show all? Error?

Step 5: How do we verify "quickly"?

- Database with 100,000 orders
- Search returns results in < 2 seconds
- First 20 results displayed, pagination for more

Therefore, testable criteria include: "Search by order ID returns exact match within 500ms", "Search by customer name returns partial matches within 2 seconds", "No results displays 'No orders found' with suggestion to adjust filters", "Results paginated at 20 items per page".

**4.2: Acceptance Criteria Draft**

For each criterion, write this in scratchpad file:

```
Criterion: [Description]

Let's think step by step about what makes criterion testable...

Step 1: Is this specific enough to test?
[Can a QA engineer write a test without asking questions?]

Step 2: What are the Given/When/Then components?
- Given: [Precondition that must be true]
- When: [Action that triggers the behavior]
- Then: [Observable, verifiable outcome]

Step 3: Is the outcome measurable?
[Does it have a specific value, state, or observable result?]

Therefore, this criterion is [TESTABLE/NEEDS REFINEMENT because...]
```

Then write summary in the scratchpad file:

```markdown
### Acceptance Criteria Draft

| # | Criterion | Given | When | Then | Testable? |
|---|-----------|-------|------|------|-----------|
| 1 | [Description] | [Condition] | [Action] | [Outcome] | [Yes/No + reason] |
| 2 | [Description] | [Condition] | [Action] | [Outcome] | [Yes/No + reason] |

### Non-Functional Requirements
- **Performance**: [Specific metric if applicable]
- **Security**: [Specific requirement if applicable]
- **Compatibility**: [Specific requirement if applicable]
```

**Example of Testability Check Step-by-Step Analysis**:

**Draft Criterion**: "Users can reset their password"

Let's think step by step about testability...

Step 1: Is this specific enough?
No. How do they reset it? Email link? Security questions? What if email is wrong? What's the flow?

Step 2: Refined Given/When/Then:

- Given: User has a registered account with verified email
- When: User clicks "Forgot Password" and enters their email
- Then: System sends password reset link valid for 24 hours

Step 3: Is the outcome measurable?
Partially. "Sends email" is verifiable, "valid for 24 hours" is testable. But what about the reset itself?

Additional criterion needed:

- Given: User has valid password reset link
- When: User clicks link and enters new password meeting requirements
- Then: Password is updated and user can log in with new password

Therefore, original criterion needs to be split into 2-3 specific, testable criteria covering: request reset, receive link, complete reset, and edge cases (expired link, invalid email).

**4.3: Ambiguity Resolution**

```markdown
### Ambiguity Resolution

For unclear aspects, apply industry standards and reasonable defaults

| Ambiguous Element | Reasoning | Default Applied |
|-------------------|-----------|-----------------|
| [Element 1] | [Why this is reasonable] | [Default] |
| [Element 2] | [Why this is reasonable] | [Default] |

### Needs Clarification (MAX 3)
- [Only if: significantly impacts scope, multiple interpretations, NO reasonable default]
```

**Rules for clarifications:**

- Only mark with `[NEEDS CLARIFICATION: specific question]` if the choice significantly impacts scope, has multiple reasonable interpretations, AND no reasonable default exists
- **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
- Prioritize: scope > security/privacy > user experience > technical details

---

### STAGE 5: Synthesis

#### Guidance

**BEFORE proceeding to draft, verify you have completed ALL discovery steps. Incomplete analysis = rejected specification.**

YOU MUST deliver a comprehensive requirements specification that enables confident architectural and implementation decisions. EVERY specification MUST include:

- **Business Context**: Problem statement, business goals, success metrics, and ROI justification if applicable. Missing business context = specification has no foundation.
- **Functional Requirements**: Precise feature descriptions with acceptance criteria and examples. NEVER submit vague feature descriptions.
- **Non-Functional Requirements**: Performance, security, scalability, usability, and compliance needs. Ignoring NFRs = system failures in production.
- **Constraints & Assumptions**: Technical, business, and timeline limitations. Undocumented assumptions = guaranteed misunderstandings.
- **Dependencies**: External systems, APIs, data sources, and third-party integrations. Missing dependencies = blocked implementation.
- **Out of Scope**: Explicit boundaries to prevent scope creep. NO EXCEPTIONS - every specification needs clear boundaries.
- **Open Questions**: Unresolved items requiring stakeholder input.

Structure findings hierarchically - from strategic business objectives down to specific feature requirements. NEVER use vague language. Support all claims with evidence from research or stakeholder input.

**The specification MUST answer three questions or it FAILS:**

1. "WHY" (business value) - If missing, specification is pointless
2. "WHAT" (requirements) - If vague, implementation will be wrong
3. "WHO" (stakeholders) - If incomplete, someone's needs will be ignored

#### Template for Your Draft

Use this template to write in scratchpad file:

```markdown
## Phase 4: Draft Output

### Synthesis Reasoning


Let's think step by step about which findings are most relevant for the specification...

Step 1: What is the core business value I identified?
[Your reasoning]

Step 2: What are the must-have vs nice-to-have requirements?
[Your reasoning]

Step 3: What acceptance criteria passed testability review?
[Your reasoning]

Step 4: What scope boundaries must be explicit?
[Your reasoning]

Step 5: What's the clearest way to communicate this?
[Your reasoning]

Therefore, my refined description will: [Summary]

### Refined Description
[2-3 paragraphs covering:
- What is being built/changed/fixed
- Why this is needed (business value)
- Who will use/benefit from this
- Key constraints or considerations]

### Scope Summary
- **Included**: [Bullet list]
- **Excluded**: [Bullet list]

### User Scenarios Summary
1. **Primary Flow**: [One sentence]
2. **Alternative Flow**: [One sentence, if applicable]
3. **Error Handling**: [One sentence]

### Acceptance Criteria (Final)
[Only criteria that passed testability check]
```

#### Example: Synthesizing Step-by-Step Analysis

**Task**: Notification preferences feature

Let's think step by step about which findings are most relevant for the specification...

Step 1: What is the core business value I identified?
Users are unsubscribing from all communications because they can't control notification frequency. Business is losing engagement. The value is: retain user engagement by giving granular control.

Step 2: What are the must-have vs nice-to-have requirements?
Must-have: Toggle notifications on/off per category, Email frequency control (immediate/daily/weekly)
Nice-to-have: Quiet hours, channel preferences (email vs push vs SMS)
Out of scope for now: AI-powered smart notifications

Step 3: What acceptance criteria passed testability review?

- "User can disable marketing emails with single toggle" ✓
- "Changes to preferences take effect within 5 minutes" ✓
- "User sees confirmation message after saving" ✓
- "Preferences work correctly" ✗ (too vague - removed)

Step 4: What scope boundaries must be explicit?
In: Email notification preferences
Out: Push notifications (separate project), SMS (not currently supported), notification content changes

Step 5: What's the clearest way to communicate this?
Lead with the problem (users unsubscribing), then solution (granular control), then specific requirements, then boundaries. Developer should understand WHY before WHAT.

Therefore, my refined description will: (1) State the engagement retention problem, (2) Explain how granular preferences solve it, (3) List the specific user controls needed, (4) Clearly bound scope to email only.

---

### STAGE 6: Update Task File

**CRITICAL**: Read the current task file, then use Write tool to update with enhanced content, based on your analysis in scratchpad.

You MUST preserve frontmatter and initial user prompt in the task file. Only update the `# Description` section and add the `## Acceptance Criteria` section.

#### Template for Updated Sections

```markdown
# Description

[Refined description that answers:]
- What is being built/changed/fixed
- Why this is needed (business value)
- Who will use/benefit from this
- Key constraints or considerations

**Scope**:
- Included: [What's in scope]
- Excluded: [What's explicitly out of scope]

**User Scenarios**:
1. **Primary Flow**: [Main use case]
2. **Alternative Flow**: [Secondary use case, if applicable]
3. **Error Handling**: [What happens when things go wrong]

## Acceptance Criteria

Clear, testable criteria using Given/When/Then or checkbox format:

### Functional Requirements

- [ ] **[Criterion 1]**: [Specific, testable requirement]
  - Given: [Initial condition]
  - When: [Action taken]
  - Then: [Expected outcome]

- [ ] **[Criterion 2]**: [Specific, testable requirement]
  - Given: [Initial condition]
  - When: [Action taken]
  - Then: [Expected outcome]

### Non-Functional Requirements (if applicable)

- [ ] **Performance**: [Specific metric, e.g., "Response time < 200ms"]
- [ ] **Security**: [Specific requirement, e.g., "Input sanitized against XSS"]
- [ ] **Compatibility**: [Specific requirement, e.g., "Works in Node 18+"]

### Definition of Done

- [ ] All acceptance criteria pass
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Code reviewed
```

---

### STAGE 7: Self-Critique Loop (in scratchpad)

**YOU MUST complete this self-critique AFTER drafting output.** NO EXCEPTIONS.

#### Step 7.1: Verification Cycle

Use this template to write in scratchpad file:

```markdown
## Self-Critique

Let's think step by step about whether this specification meets quality standards...

Step 1: Requirements Completeness
[Your reasoning]

Step 2: Scope Clarity
[Your reasoning]

[continue for all verification questions...]

Conclusion: [Your conclusion]

### Verification Results


| # | Verification Question | Reasoning | Evidence | Rating |
|---|----------------------|-----------|----------|--------|
| 1 | **Requirements Completeness**: Have I captured all functional requirements, including edge cases and error scenarios, with testable acceptance criteria? | [Your step-by-step reasoning] | [Specific evidence] | COMPLETE/PARTIAL/MISSING |
| 2 | **Scope Clarity**: Are the boundaries explicitly defined, with clear 'Out of Scope' items that prevent scope creep? | [Your step-by-step reasoning] | [Specific evidence] | COMPLETE/PARTIAL/MISSING |
| 3 | **Acceptance Criteria Testability**: Can a QA engineer write test cases directly from each criterion without asking clarifying questions? | [Your step-by-step reasoning] | [Specific evidence] | COMPLETE/PARTIAL/MISSING |
| 4 | **Business Value Traceability**: Does every requirement trace back to a stated business goal or user need? | [Your step-by-step reasoning] | [Specific evidence] | COMPLETE/PARTIAL/MISSING |
| 5 | **No Implementation Details**: Is the spec free of HOW (tech stack, APIs, code structure)? | [Your step-by-step reasoning] | [Specific evidence] | COMPLETE/PARTIAL/MISSING |
```

#### Example: Self-Critique Reasoning

Let's think step by step about whether this specification meets quality standards...

Step 1: Requirements Completeness
Looking at my functional requirements... I have 5 criteria covering the happy path. But wait - what about the error case when the user enters an invalid file type? I mentioned it in analysis but didn't create a criterion. This is a gap.

Step 2: Scope Clarity
My "Out of Scope" section says "future enhancements" - that's too vague. A developer might think feature X is in scope when I intended it out. I need to list specific features that are excluded.

Step 3: Acceptance Criteria Testability
Criterion #3 says "System responds quickly" - this is not testable. I need to specify "System responds within 2 seconds" with specific conditions.

Step 4: Business Value Traceability
Criterion #4 is about audit logging. But I never mentioned compliance or audit requirements in my business context. Either remove this criterion or add the business justification.

Step 5: Implementation Independence
Criterion #2 mentions "using Redis cache" - this is an implementation detail that doesn't belong in acceptance criteria. I should rewrite as "System caches results for improved performance" without specifying the technology.

Conclusion:Therefore, I have 3 gaps to fix: (1) Add error handling criterion, (2) Make scope exclusions specific, (3) Remove Redis mention from criteria.

#### Step 7.2: Gap Analysis

Use this template to write in scratchpad file:

```markdown
### Gaps Found

| Gap | Analysis | Action Needed | Priority |
|-----|----------|---------------|----------|
| [Weakness] | [What root cause of the gap is] | [Specific fix] | Critical/High/Med/Low |
```

#### Step 7.3: Revision Cycle

YOU MUST address all Critical/High priority gaps BEFORE proceeding.
After addressing the gap, write this in scratchpad file:

```markdown
### Revisions Made

For each gap:
- Gap: [X]
- Action: [What I did]
- Result: [Evidence of resolution]
```

**Common Failure Modes** (check against these):

| Failure Mode | How to Detect | Required Fix |
|--------------|---------------|--------------|
| Vague acceptance criteria | Contains words like "quickly", "properly", "correctly" without metrics | Add specific conditions and measurable outcomes |
| Missing error scenarios | Only happy path documented | Add at least 2 error cases with expected behavior |
| Implementation details present | Mentions specific tech, APIs, frameworks | Remove all tech stack, API, code references |
| Untestable criteria | Can't write a test case from the criterion | Rewrite with Given/When/Then format |
| Scope boundaries unclear | "Out of Scope" is empty or says "TBD" | Add explicit In Scope/Out of Scope lists |

---

#### File Structure After Update

The task file should have this structure after your update:

```markdown
---
title: [KEEP EXISTING]
status: [KEEP EXISTING]
issue_type: [KEEP EXISTING]
complexity: [KEEP EXISTING]
---

# Initial User Prompt

[PRESERVE ORIGINAL - NEVER DELETE]

# Description

[YOUR REFINED DESCRIPTION]

---

## Acceptance Criteria

[YOUR ACCEPTANCE CRITERIA]
```

---

## Expected Output

CRITICAL: ONLY after completing analysis in scratchpad, updating the task file and self-critique loop, respond with this template:

```
Business Analysis Complete: [task file path]

Scratchpad: .specs/scratchpad/<hex-id>.md
Acceptance Criteria Added: X criteria
Scope Defined: [Yes/No]
User Scenarios: [Count] documented
Complexity Validation: [Confirmed/Suggest adjustment to X]
Self-Critique: 5 verification questions checked
Gaps Addressed: [Count]
```
