# test-coverage - Test Coverage Analysis Reference Manual

Manual for choosing, applying, different types of coverage analysis on an existing test suite

> Distills structural, mutation, requirements, API/integration, and specification-domain coverage techniques into per-type decision tables, asymmetry-aware thresholds, and ecosystem toolchain references.

## Use When

Use **after** tests are already written — when you need to assess how well an existing suite exercises the code or specification along one or more axes. It does **not** tell you when to write tests or which test types to design (that is the job of [`design-testing-strategy`](./design-testing-strategy.md)). It tells you, once tests exist, *which mechanical signal best measures what those tests do (and do not) exercise*, and how to read that signal honestly.

| Use when... | Skip when... |
|-------------|--------------|
| Choosing a coverage metric for a new module or codebase | You have not written tests yet — design the strategy first |
| Interpreting a coverage report (line, branch, mutation, RTM, API) | You only need to know *what* to test, not *how to measure* an existing suite |
| Setting a CI gate, threshold, or delta target | The task is a one-off script with no regression risk |
| Diagnosing why "high coverage" still produces production bugs | You are in a regulated domain — defer to the standard, not this skill |
| Picking a tool per ecosystem (JS, Python, JVM, Go, .NET, C/C++, Rust, etc.) | Coverage is being chased as a target rather than used as a tripwire |

## Core Principles

| Principle | One-line explanation |
|-----------|---------------------|
| **Coverage is a measurement, not a test type** | Mutation, MC/DC, branch, RTM, contract, schema coverage are *measurements about* an existing suite — not test types like unit/integration/e2e. |
| **Asymmetry of evidence** | Low coverage is strong evidence of weak testing; high coverage is weak evidence of strong testing. |
| **Necessary but not sufficient** | A line can execute without any assertion verifying behavior. 100% line coverage with zero assertions is routine. |
| **Tripwire, not trophy** | Treat coverage as a floor and a regression detector — never as the goal itself (Goodhart's law). |
| **Risk-proportional targets** | The same artifact at different criticalities should not share a coverage gate. |
| **Combining axes is multiplicative** | Each axis closes blind spots the others structurally cannot see; layering > raising any single number. |

## Coverage Taxonomy

| Family | Axis | What it measures |
|--------|------|------------------|
| **Structural / code** | Line / Statement | Lines executed at least once |
| | Branch / Decision | True/false outcomes of every decision exercised |
| | Condition | Every Boolean sub-condition has been both T and F |
| | MC/DC | Each condition independently affects the decision outcome (regulated) |
| | Function / Method | Every declared function invoked |
| | Path | Linearly-independent paths through a function (rarely practical) |
| **Mutation** | Mutation score | Proportion of injected source faults the suite detects |
| **Requirements / feature** | RTM / AC linkage | Every acceptance criterion has at least one verifying test |
| | BDD scenarios | Gherkin `Scenario:` blocks aligned to ACs |
| **API / integration** | Endpoint | `(method, path_template, status)` triples exercised |
| | Contract (CDC) | Consumer-recorded interactions verified by the provider |
| | Schema | OpenAPI / JSON Schema / GraphQL fields, enums, variants exercised |
| | Integration-path | Service-to-service edges exercised end-to-end |
| **Specification-domain** | Data / Equivalence-class | Equivalence partitions and BVA `(B-1, B, B+1)` slots |
| | Pairwise / Combinatorial | All pairs (or t-way) of parameter values combined |
| | Exception / Error-path | `catch` / `Result.Err` / `if err != nil` branches |
| | State / Transition | 0-switch / 1-switch / round-trip transitions in a state machine |

Each coverage type in the skill is documented in the **same six sub-fields**: `Definition`, `What it does NOT measure`, `Typical tools`, `When to use vs skip`, `Targets / thresholds & pitfalls`, `Cost-benefit ROI`.

## Decision References

The skill includes lookup tables for fast retrieval — read only the row that matches your situation.

| Reference table | Use for |
|-----------------|---------|
| **Coverage methods by criticality** | NONE → LOW → MEDIUM → MEDIUM-HIGH → HIGH → Regulated, with recommended signals per row |
| **Coverage methods by artifact type** | Pure utility, HTTP endpoint, UI component, workflow engine, authorization module, multi-parameter config, public API, library, generated code |
| **Ecosystem toolchain quick-reference** | JS/TS, JVM, Python, Go, .NET, Ruby, C/C++, Rust, PHP — structural / mutation / API / combinatorial / BDD tool per cell |
| **Regulated-domain standards** | DO-178C, ISO 26262, IEC 62304, MISRA, EN 50128, IEC 61508 — required coverage per criticality level |
| **UI / interaction coverage extras** | Playwright traces, Storybook stories, visual regression baselines |

## Cross-Cutting Topics

| Topic | What the skill provides |
|-------|------------------------|
| **The weak-assertion pitfall** | Worked examples of green-but-useless tests; mutation as the only practical counter-measure for assertion strength |
| **Common gaming patterns** | 10 anti-patterns (assertion-free tests, snapshot inflation, dead-code coverage, try/catch suppression, one-line condensation, silent exclusions, generated-code inflation, RTM gaming, stale traces) and counter-measures |
| **Risk-based interpretation** | Criticality-to-threshold table; delta thresholds preferred over absolute floors |
| **Instrumentation caveats** | Coverage-build ≠ release-build; concurrent execution data loss; native code via FFI/JNI; stale hot-reload coverage |
| **Layered coverage stack** | Default stack for non-regulated product code: branch + AC linkage + nightly mutation on pure-logic core + pairwise on config + contract/endpoint + state-transition for workflows |

## Relationship to Other TDD Skills

| Skill | When to use |
|-------|------------|
| [`test-driven-development`](./test-driven-development.md) | While writing the production code — Red-Green-Refactor cycle, anti-pattern detection |
| [`design-testing-strategy`](./design-testing-strategy.md) | Before writing tests — pick which test types to design for a given artifact |
| `test-coverage` (this skill) | After tests exist — measure what the suite does and does not exercise, and how to read the report |

These three skills are orthogonal: strategy decides *what* to test, TDD governs *how* to write tests, and coverage analysis decides *how to measure* the result.

## Sources & Further Reading

The skill cites primary sources for every coverage type and standard, including:

- **Standards** — DO-178C, ISO 26262, IEC 62304, MISRA C/C++, ISO/IEC/IEEE 29119, ISTQB Foundation Level (BVA, RTM).
- **Structural & MC/DC** — LDRA, Wikipedia MC/DC, Qt Coco, cyclomatic complexity references.
- **Mutation testing** — Stryker (JS/.NET/Scala), PIT (JVM), mutmut / Cosmic Ray (Python), go-mutesting, Infection (PHP), Mull (C/C++), cargo-mutants (Rust), Microsoft Learn on mutation testing.
- **API / contract** — Pact, Pactflow, Spring Cloud Contract, Specmatic, Schemathesis, Dredd.
- **Combinatorial / state / UI** — Microsoft PICT, NIST ACTS, Playwright trace viewer, Storybook Test, Chromatic.
- **Industry commentary** — "The Fallacy of the 100% Code Coverage" (thinkinglabs.io), "Code Coverage Targets — Recipe for Disaster" (Optivem Journal), "Is 70/80/90/100% coverage good enough?" (Qt), "AI-Generated Tests Give False Confidence" (codeintelligently.com).

Full source list with hyperlinks is embedded in the skill itself.
