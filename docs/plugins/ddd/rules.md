# Rules Reference

The DDD plugin enforces code quality through 14 rules that activate automatically when writing or reviewing code. Each rule targets specific files via glob patterns and has an assigned impact level.

Rules replace the previous monolithic `software-architecture` skill with focused, composable guidelines that Claude applies contextually based on the files being edited.

## Rules Overview

| Rule | Impact | Scope | Description |
|------|--------|-------|-------------|
| [Clean Architecture & DDD](#clean-architecture--ddd) | HIGH | `src/**/*` | Separate domain logic from infrastructure |
| [Separation of Concerns](#separation-of-concerns) | HIGH | `src/**/*` | Enforce boundaries between layers |
| [Functional Core, Imperative Shell](#functional-core-imperative-shell) | HIGH | `src/**/*` | Pure business logic, side effects at the edges |
| [Command-Query Separation](#command-query-separation) | HIGH | `src/**/*` | Functions either return or mutate, never both |
| [Explicit Control Flow](#explicit-control-flow) | HIGH | `src/**/*` | Control flow decisions visible at call site |
| [Explicit Data Flow](#explicit-data-flow) | HIGH | `src/**/*` | Return values over input mutation |
| [Explicit Side Effects](#explicit-side-effects) | HIGH | `src/**/*` | Side effects visible where triggered |
| [Principle of Least Astonishment](#principle-of-least-astonishment) | HIGH | `src/**/*` | Functions do only what their name promises |
| [Error Handling](#error-handling) | HIGH | `src/**/*` | Typed errors, never silently swallowed |
| [Domain-Specific Naming](#domain-specific-naming) | HIGH | `**/*` | No `utils`, `helpers`, `common` |
| [Library-First Approach](#library-first-approach) | HIGH | `**/*` | Search for existing solutions before custom code |
| [Early Return Pattern](#early-return-pattern) | MEDIUM | `**/*` | Guard clauses reduce nesting |
| [Call-Site Honesty](#call-site-honesty) | MEDIUM | `src/**/*` | Logging visible at call site |
| [Function & File Size Limits](#function--file-size-limits) | MEDIUM | `**/*` | Functions <80 lines, files <200 lines |

## Architecture Rules

### Clean Architecture & DDD

Keep business logic in pure domain and use case layers, free of framework or infrastructure dependencies.

**Key principles:**

- **Domain Layer** - Business entities independent of frameworks
- **Use Case Layer** - Application-specific business rules
- **Interface Layer** - Controllers, presenters, gateways
- **Infrastructure Layer** - Frameworks, databases, external services
- Domain must never import from infrastructure
- Use abstract repository interfaces for dependency inversion

### Separation of Concerns

Do NOT mix business logic with UI components or place database queries directly in controllers. Maintain clear architectural boundaries.

**Layer responsibilities:**

| Layer | Handles | Does NOT handle |
|-------|---------|-----------------|
| Controllers | HTTP concerns, request/response | Business rules, database queries |
| Services | Business logic, orchestration | HTTP details, data persistence |
| Repositories | Data access, query building | Business decisions, HTTP concerns |

### Functional Core, Imperative Shell

Keep business logic in pure functions; push all side effects to an outer imperative shell that orchestrates the core.

- **Pure core** - Deterministic, no side effects, testable without mocks
- **Imperative shell** - Handles I/O (database, HTTP, logging, file I/O)
- Enables easy composition, parallelization, and testing

## Function Design Rules

### Command-Query Separation

Functions must either return a value (query) or cause a side effect (command), never both. Mutations hidden by assignments are anti-patterns.

### Principle of Least Astonishment

Functions must do exactly what their name and signature suggest. No hidden side effects or unexpected behavior:

- `getUser` must not mutate state
- Pure queries don't throw
- All side effects explicit at call site
- Clearly named wrappers advertise combined behavior

### Call-Site Honesty

Logging calls must be visible and explicit at the call site, not buried inside utility functions. Separate policy (when/whether to log) from mechanism (how to format).

## Explicitness Rules

### Explicit Control Flow

Error conditions and control flow decisions must be visible at the call site, never hidden inside helper functions. Pure functions (mechanisms) return values; the caller decides policy (throw, log, branch).

### Explicit Data Flow

If a function produces a result, return it explicitly. Never rely on mutation of input parameters to communicate output. Use `const` for assignments and prefer pure expressions over procedures.

### Explicit Side Effects

Make side effects visible where they are triggered. Orchestration should be a transparent table of contents — each side effect (persistence, notifications, external calls) as a distinct line, readable without drilling into implementations.

## Code Quality Rules

### Error Handling

Never silently swallow exceptions. Use typed error handling and log all errors with context before rethrowing:

- Typed catch blocks distinguishing domain vs. system errors
- Log with sufficient context (operation name, IDs)
- Extract complex error handling into reusable handlers
- Distinguish between expected and unexpected failures

### Domain-Specific Naming

Avoid generic module names. Use domain-specific names that reflect bounded contexts:

| Avoid | Prefer | Reason |
|-------|--------|--------|
| `utils.js` | `OrderCalculator.js` | Domain-specific purpose |
| `helpers/misc.js` | `UserAuthenticator.js` | Clear responsibility |
| `common/shared.js` | `InvoiceGenerator.js` | Single bounded context |

### Library-First Approach

Always search for existing libraries or services before writing custom code. Custom code is justified only for:

- Domain-specific business logic
- Performance-critical paths with special requirements
- Security-sensitive code requiring full control
- Cases where existing solutions don't meet requirements after thorough evaluation

### Early Return Pattern

Use early returns for error conditions and edge cases to reduce nesting and keep the happy path visible. Guard clauses at function start, maximum 3 levels of nesting.

### Function & File Size Limits

Decompose functions longer than 80 lines (target: 50 lines each) and keep files under 200 lines. Each function should serve a single purpose. Extract cohesive blocks into named functions when limits are exceeded.
