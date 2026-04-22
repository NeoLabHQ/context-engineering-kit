# TypeScript Best Practices Rule

Auto-applied rule that enforces TypeScript coding standards whenever the agent reads or writes TypeScript files. Covers type system guidelines, code style patterns, async best practices, and utility type usage.

- Activation - Automatically when working on files matching `**/*.ts`
- Impact - Applied to all TypeScript file operations (read and write)

## What It Enforces

The rule provides comprehensive TypeScript guidelines organized into seven categories. When plugin is active, the agent receives these standards as context on first read or write of a TypeScript file.

### Categories

| Category | Key Guidelines |
|----------|---------------|
| **Code Style** | Strict typing, interfaces over types for object shapes, enums for constants, type guards over assertions |
| **Type System** | Prefer inference, avoid `any`, use `Record<PropertyKey, unknown>` over `object`, prefer `@ts-expect-error` over `@ts-ignore` |
| **Async Patterns** | `async`/`await` over callbacks, async APIs over sync, `Promise.all` for concurrency |
| **Code Structure** | Object destructuring, descriptive naming, named constants over magic values |
| **Type Narrowing** | typeof guards, instanceof guards, truthiness/equality narrowing, `in` operator, custom type guards (type predicates, generics, property checks), assertion functions |
| **TypeScript Utility Types** | Parameters, ReturnType, Awaited, Record, Partial, Required, Omit, Pick, Exclude, Extract, NonNullable, plus reusable wrapper type patterns |
| **Performance** | `for...of` over index loops, reuse existing functions and packages |
| **Logging** | Never log private data, always log errors in `.catch()` callbacks |
| **Time Consistency** | Assign `Date.now()` once and reuse, use `ms` package for durations |

### Type System Guidelines

The rule emphasizes strict type safety with specific preferences:

- **Interfaces for objects, types for unions** - Use `interface` for object shapes (e.g., React props); use `type` for unions and intersections
- **Const assertions** - Prefer `as const satisfies XyzInterface` over plain `as const`
- **Module augmentation** - Prefer `declare module` over `namespace`-based extension patterns
- **Extensibility** - Define metadata fields next to the processor/plugin that reads or writes them

### Library-First Approach

The rule recommends established libraries over custom implementations:

| Domain | Recommended Libraries |
|--------|----------------------|
| Date/time | date-fns, dayjs |
| Validation | joi, yup, zod |
| HTTP | axios, got |
| State management | Redux, MobX, Zustand |
| Utilities | lodash, ramda |

### Type Narrowing

The rule covers TypeScript's ability to refine types based on control flow analysis. When the agent writes conditional logic, it applies these narrowing techniques:

| Technique | Description |
|-----------|-------------|
| `typeof` guards | Narrow primitives (`string`, `number`, `boolean`, etc.) |
| `instanceof` guards | Narrow class instances (e.g., `Error`, custom classes) |
| Truthiness narrowing | Eliminate `null`/`undefined` via truthy checks |
| Equality narrowing | Refine types when two values are compared with `===` |
| `in` operator | Discriminate union members by checking for a property |
| Custom type guards | User-defined `value is Type` predicate functions |
| Generic type guards | Reusable guards like `isNotNull<T>` for filtering arrays |
| Object property checks | `hasProperty` guards for safe dynamic property access |
| Assertion functions | `asserts value is Type` functions that throw on invalid input |

### TypeScript Utility Types

The rule provides practical usage patterns and before/after examples for built-in utility types. The agent uses these when generating or refactoring type definitions:

| Utility Type | Use Case |
|-------------|----------|
| `Parameters<T>` | Wrapping functions, creating function variants |
| `ReturnType<T>` | Extracting return types when not explicitly exported |
| `Awaited<T>` | Unwrapping Promise types, especially with async functions |
| `Record<K, V>` | Creating object types with dynamic or union keys |
| `Partial<T>` | Update/patch operations where not all fields are required |
| `Required<T>` | Ensuring all config options are provided |
| `Omit<T, K>` | Removing sensitive or internal fields from types |
| `Pick<T, K>` | Creating focused subsets of larger types |
| `Exclude<T, U>` | Filtering members out of union types |
| `Extract<T, U>` | Selecting specific members from union types |
| `NonNullable<T>` | Removing `null`/`undefined` after validation |

Also includes patterns for combining utilities (e.g., `Awaited<ReturnType<typeof fn>>`) and creating reusable wrapper types.

### Code Examples Included

The rule contains before/after examples for common TypeScript patterns:

- Eliminating `any` with generics
- Narrowing unknown API responses with type guards
- `as const` assertions and literal types
- Conditional types and `infer` keyword
- Mapped types and opaque (brand) types
- Template literal types
