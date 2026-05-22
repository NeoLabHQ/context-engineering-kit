# design-testing-strategy - Testing Strategy Reference Manual

Manual for agents that need to decide what best way to cover a given artifact with tests, while minimizing amount of work.

> Distills 15 industry-recognized testing methodology sources into deterministic decision gates, an enforced YAML matrix schema, and three end-to-end worked examples.

## When to Use

Use when:

- Designing a test plan for a new feature, change, or refactor.
- Reviewing an existing test suite for adequacy or over-investment.
- Covering new functionality with tests.

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

```bash
> /design-testing-strategy for ./AuthenticationService.ts
```