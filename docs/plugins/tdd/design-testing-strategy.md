# design-testing-strategy - Testing Strategy Reference Manual

On-demand reference manual loaded by qa-engineer, developer, code-reviewer, and judge agents that need to decide WHICH test types to write, at WHAT size, with WHICH dependencies, and WHICH ones to deliberately skip.

Distills 15 industry-recognized testing methodology sources into deterministic decision gates, an enforced YAML matrix schema, and three end-to-end worked examples.

## When to Load

Load on demand (not on every prompt) when:

- Designing a test plan for a new feature, change, or refactor.
- Reviewing an existing test suite for adequacy or over-investment.
- Producing `test_strategy` YAML matrices for `/sdd:plan` verification phases.
- Auditing a PR's testing approach as a code-reviewer or judge.

## Key Sections

| Section | Purpose |
|---------|---------|
| **Decision Gates** | 7 deterministic gates (Skip / Unit / Integration / Component-or-E2E / Contract / Smoke / Property-Based / Mutation) applied in order. Each gate has explicit ON-when / OFF-when criteria with source citations. |
| **Test Type Reference** | Per-type guidance: when to use, when NOT to use, frameworks, dependencies, Google test-size mapping (small/medium/large/enormous). |
| **Case Design Techniques** | ISTQB Equivalence Partitioning, Boundary Value Analysis (B-1, B, B+1), Decision Tables, State Transition — each with a worked example. |
| **Dependency Decision** | When to use Testcontainers vs in-memory fakes vs mocks vs stubbed HTTP vs real services; Playwright vs Cypress for UI. |
| **Strategic Skip Heuristics** | Explicit "don't bother with X when Y" rules grounded in risk-based testing (ISO/IEC/IEEE 29119). |
| **Test Matrix Schema** | Enforced YAML schema for the `test_strategy` block. Field ordering is load-bearing: `rationale -> type` in `selected_types`, `reason -> type` in `rejected_types`, `why -> what` in `deliberately_skipped`. |
| **Case Listing Schema** | Markdown bullet list format `- [type] description (AC-N)` for the test cases to be implemented. |
| **Sources & Further Reading** | All 15 cited sources as markdown hyperlinks. |
| **Worked Examples** | (A) Pure helper function `formatCurrency`, (B) HTTP POST endpoint with DB and multi-consumer (`POST /users`), (C) UI form component (`<RegistrationForm />`). |

## Sources Distilled

1. Test Pyramid (Cohn / Vocke)
2. Testing Trophy (Kent C. Dodds)
3. Google Test Sizes (Bland / SWE at Google Ch.11)
4. Google "Testing on the Toilet"
5. ISTQB Foundation Level black-box techniques
6. ISO/IEC/IEEE 29119 risk-based testing
7. Kent Beck — *Test Driven Development: By Example*
8. The Pragmatic Programmer (20th Anniversary Edition)
9. AAA / Given-When-Then (Wake / North)
10. Property-based testing (Hypothesis / QuickCheck)
11. Contract testing / Consumer-Driven Contracts (Pact)
12. Testcontainers
13. Mutation testing (Stryker / PIT)
14. Table-driven tests (Cheney)
15. Risk-based testing

## How To Use

1. Read **Decision Gates** in order (Gate 0 -> Gate 7). Each gate is independent — you may finish with any subset of test types ON.
2. Apply **Strategic Skip Heuristics** to remove ON gates that would yield low ROI.
3. For each ON gate, fill the **Test Matrix Schema** (`selected_types` entry) — field order is load-bearing.
4. List rejected types in `rejected_types` and deliberate skips in `deliberately_skipped`.
5. Produce a **Test Cases to Cover** markdown list using ISTQB techniques from **Case Design Techniques**.
6. Cross-check against the matching **Worked Example**.

See the full skill at [`plugins/tdd/skills/design-testing-strategy/SKILL.md`](https://github.com/NeoLabHQ/context-engineering-kit/blob/master/plugins/tdd/skills/design-testing-strategy/SKILL.md).
