---
title: TypeScript Best Practices
paths:
  - "**/*.ts"
---

# TypeScript Best Practices

## Code Style Rules

### General Principles

- **TypeScript**: All code must be strictly typed, leverage TypeScript's type safety features

### Code style rules

- Interfaces over types - use interfaces for object types
- Use enum for constant values, prefer them over string literals
- Export all types by default
- Use type guards instead of type assertions

### Best Practices

#### Library-First Approach

- Common areas where libraries should be preferred:
  - Date/time manipulation → date-fns, dayjs
  - Form validation → joi, yup, zod
  - HTTP requests → axios, got
  - State management → Redux, MobX, Zustand
  - Utility functions → lodash, ramda

#### Code Quality

- Use destructuring of objects where possible:
  - Instead of `const name = user.name` use `const { name } = user`
  - Instead of `const result = await getUser(userId)` use `const { data: user } = await getUser(userId)`
  - Instead of `const parseData = (data) => data.name` use `const parseData = ({ name }) => name`
- Use `ms` package for time related configuration and environment variables, instead of multiplying numbers by 1000


## Types and Type Safety

- Avoid explicit type annotations when TypeScript can infer
- Avoid implicitly `any`; explicitly type when necessary
- Use accurate types: prefer `Record<PropertyKey, unknown>` over `object` or `any`
- Prefer `interface` for object shapes (e.g., React props); use `type` for unions/intersections
- Prefer `as const satisfies XyzInterface` over plain `as const`
- Prefer `@ts-expect-error` over `@ts-ignore` over `as any`
- Avoid meaningless null/undefined parameters; design strict function contracts
- Prefer ES module augmentation (`declare module '...'`) over `namespace`; do not introduce `namespace`-based extension patterns
- When a type needs extensibility, expose a small mergeable interface at the source type and let each feature/plugin augment it locally instead of centralizing all extension fields in one registry file
- For package-local extensibility patterns like `PipelineContext.metadata`, define the metadata fields next to the processor/provider/plugin that reads or writes them

## Async Patterns

- Prefer `async`/`await` over callbacks or `.then()` chains
- Prefer async APIs over sync ones (avoid `*Sync`)
- Use promise-based variants: `import { readFile } from 'fs/promises'`
- Use `Promise.all`, `Promise.race` for concurrent operations where safe

## Code Structure

- Prefer object destructuring
- Use consistent, descriptive naming; avoid obscure abbreviations
- Replace magic numbers/strings with well-named constants
- Defer formatting to tooling


## Performance

- Prefer `for…of` loops over index-based `for` loops
- Reuse existing functions and logic from codebase or installed npm packages

## Time Consistency

- Assign `Date.now()` to a constant once and reuse for consistency

## Logging

- Never log user private information (API keys, etc.)
- Always log the error in `.catch()` callbacks — silent `.catch(() => fallback)` swallows failures and makes debugging impossible


# Quick Examples

## Eliminating `any` with generics

**Before**
```ts
function getProperty(obj: any, key: string): any {
  return obj[key];
}
```

**After**
```ts
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}
// getProperty({ name: "Alice" }, "name") → inferred as string ✓
```

## Narrowing an unknown API response

**Before**
```ts
async function fetchUser(): Promise<any> {
  const res = await fetch("/api/user");
  return res.json();
}
```

**After**
```ts
interface User { id: number; name: string }

function isUser(value: unknown): value is User {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    "name" in value
  );
}

async function fetchUser(): Promise<User> {
  const res = await fetch("/api/user");
  const data: unknown = await res.json();
  if (!isUser(data)) throw new Error("Invalid user shape");
  return data;
}
```


## The `as const` Assertion

`as const` is a const assertion that makes an object deeply readonly and infers literal types instead of widened types.

```typescript
// Without as const - types are widened
const config = {
  GROUP: "group",
  ANNOUNCEMENT: "announcement",
};
// Type: { GROUP: string; ANNOUNCEMENT: string }

// With as const - literal types are preserved
const config = {
  GROUP: "group",
  ANNOUNCEMENT: "announcement",
} as const;
// Type: { readonly GROUP: "group"; readonly ANNOUNCEMENT: "announcement" }
```

## Array Index Access with `[number]`

Just like you can access object properties with string keys, you can access array elements with numeric indices:

```typescript
const roles = ["user", "admin", "anonymous"] as const;

// Access specific index
type FirstRole = typeof roles[0]; // "user"
type SecondRole = typeof roles[1]; // "admin"

// Access all elements with [number]
type AnyRole = typeof roles[number]; // "user" | "admin" | "anonymous"
```

## Conditional Types

```typescript
type Conditional = SomeType extends OtherType ? TrueType : FalseType;
```

The condition checks if `SomeType` is assignable to `OtherType`.

```typescript
// Check if type is string
type IsString<T> = T extends string ? true : false;

type Test1 = IsString<string>; // true
type Test2 = IsString<number>; // false
type Test3 = IsString<"hello">; // true (literal extends string)

// Check type relationships
type Result1 = string extends string ? "yes" : "no"; // "yes"
type Result2 = string extends number ? "yes" : "no"; // "no"
type Result3 = "hello" extends string ? "yes" : "no"; // "yes"
```

## Function Overloads


Function overloads allow you to define multiple function signatures for a single function implementation. TypeScript selects the appropriate signature based on the arguments provided.

```typescript
// Overload signatures (what callers see)
function greet(name: string): string;
function greet(firstName: string, lastName: string): string;

// Implementation signature (must be compatible with all overloads)
function greet(nameOrFirst: string, lastName?: string): string {
  if (lastName) {
    return `Hello, ${nameOrFirst} ${lastName}!`;
  }
  return `Hello, ${nameOrFirst}!`;
}

// Usage - TypeScript picks the right overload
greet("Alice"); // Uses first overload
greet("Alice", "Smith"); // Uses second overload
```


## Generics Fundamentals

Generics allow you to create reusable components that work with multiple types while maintaining type safety. They're essential for building flexible, type-safe APIs.

```typescript
// Without generics - loses type information
function identity(value: any): any {
  return value;
}

// With generics - preserves type
function identity<T>(value: T): T {
  return value;
}

const num = identity(42); // Type: number (inferred)
const str = identity("hello"); // Type: string (inferred)
const explicit = identity<boolean>(true); // Type: boolean (explicit)
```


## The `infer` Keyword

The `infer` keyword allows you to extract and capture type information within conditional types. It's like pattern matching for types - you define a pattern and capture parts of it.

```typescript
type ExtractType<T> = T extends SomePattern<infer U> ? U : never;
//                                          ^^^^^^^^
//                                     Captures this part into U
```

Extract Array Element Type

```typescript
type ArrayElement<T> = T extends (infer U)[] ? U : never;

type Test1 = ArrayElement<string[]>; // string
type Test2 = ArrayElement<number[]>; // number
type Test3 = ArrayElement<(string | number)[]>; // string | number
type Test4 = ArrayElement<string>; // never (not an array)
```

## Mapped Types

Mapped types allow you to create new types by transforming each property of an existing type. They iterate over keys and apply transformations to create new type structures.

```typescript
type MappedType<T> = {
  [K in keyof T]: TransformedType;
};
```

Make All Properties Optional

```typescript
type MyPartial<T> = {
  [K in keyof T]?: T[K];
};

interface User {
  id: string;
  name: string;
  email: string;
}

type PartialUser = MyPartial<User>;
// { id?: string; name?: string; email?: string }
```

## Opaque Types (Brand Types)

Opaque types (also called brand types or nominal types) create distinct types from primitive types. They prevent mixing up values that have the same underlying type but different semantic meanings.

TypeScript uses structural typing, so these are interchangeable:

```typescript
type UserId = string;
type PostId = string;

function getUser(id: UserId): User { /* ... */ }
function getPost(id: PostId): Post { /* ... */ }

const userId: UserId = "user-123";
const postId: PostId = "post-456";

// BUG: Wrong ID type, but TypeScript allows it!
getUser(postId); // No error - both are just strings
```

Add a phantom property to create nominal distinction:

```typescript
type Opaque<TValue, TBrand> = TValue & { __brand: TBrand };

type UserId = Opaque<string, "UserId">;
type PostId = Opaque<string, "PostId">;
type ValidEmail = Opaque<string, "ValidEmail">;
type ValidAge = Opaque<number, "ValidAge">;
```

Now these types are incompatible:

```typescript
function getUser(id: UserId): User { /* ... */ }
function getPost(id: PostId): Post { /* ... */ }

const userId = "user-123" as UserId;
const postId = "post-456" as PostId;

getUser(userId); // OK
getUser(postId); // Error: Type 'PostId' is not assignable to type 'UserId'
```

## Template Literal Types

Template literal types allow you to manipulate string types using the same syntax as JavaScript template literals. Combined with `infer`, they enable powerful string parsing and transformation at the type level.

```typescript
type Greeting = `Hello, ${string}`;

const valid: Greeting = "Hello, World"; // OK
const invalid: Greeting = "Hi, World"; // Error: doesn't match pattern
```

Template literals distribute over unions:

```typescript
type Size = "small" | "medium" | "large";
type Color = "red" | "blue" | "green";

type SizedColor = `${Size}-${Color}`;
// "small-red" | "small-blue" | "small-green" |
// "medium-red" | "medium-blue" | "medium-green" |
// "large-red" | "large-blue" | "large-green"
```

Extract parts of string types:

```typescript
// Remove "maps:" prefix
type RemoveMaps<T> = T extends `maps:${infer Rest}` ? Rest : T;

type Test1 = RemoveMaps<"maps:longitude">; // "longitude"
type Test2 = RemoveMaps<"maps:latitude">; // "latitude"
type Test3 = RemoveMaps<"other">; // "other"
```

## Type Narrowing

Type narrowing is TypeScript's ability to refine types based on control flow analysis. When you check a type condition, TypeScript narrows the type within that code block.

### `typeof` Guards

```typescript
function processValue(value: string | number) {
  if (typeof value === "string") {
    // value is string here
    return value.toUpperCase();
  }
  // value is number here
  return value.toFixed(2);
}
```

### `instanceof` Guards

```typescript
function logError(error: Error | string) {
  if (error instanceof Error) {
    // error is Error here
    console.log(error.stack);
  } else {
    // error is string here
    console.log(error);
  }
}
```

### Truthiness Narrowing

```typescript
function printName(name: string | null | undefined) {
  if (name) {
    // name is string here (truthy)
    console.log(name.toUpperCase());
  }
}
```

### Equality Narrowing

```typescript
function example(x: string | number, y: string | boolean) {
  if (x === y) {
    // Both are string here (only common type)
    console.log(x.toUpperCase());
    console.log(y.toUpperCase());
  }
}
```

### `in` Operator

```typescript
interface Fish {
  swim: () => void;
}

interface Bird {
  fly: () => void;
}

function move(animal: Fish | Bird) {
  if ("swim" in animal) {
    // animal is Fish here
    animal.swim();
  } else {
    // animal is Bird here
    animal.fly();
  }
}
```

### Custom Type Guards

#### Type Predicates

Functions that return `value is Type`:

```typescript
interface Fish {
  swim: () => void;
}

interface Bird {
  fly: () => void;
}

function isFish(pet: Fish | Bird): pet is Fish {
  return (pet as Fish).swim !== undefined;
}

function move(pet: Fish | Bird) {
  if (isFish(pet)) {
    // pet is Fish here
    pet.swim();
  } else {
    // pet is Bird here
    pet.fly();
  }
}
```

#### Generic Type Guards

```typescript
function isNotNull<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined;
}

const values = [1, null, 2, undefined, 3];
const filtered = values.filter(isNotNull);
// filtered is number[]
```

#### Object Property Check

```typescript
function hasProperty<T extends object, K extends string>(
  obj: T,
  key: K
): obj is T & Record<K, unknown> {
  return key in obj;
}

const data: unknown = { name: "Alice" };

if (typeof data === "object" && data !== null && hasProperty(data, "name")) {
  // data.name is now accessible
  console.log(data.name);
}
```

### Assertion Functions

Functions that throw on invalid input:

```typescript
function assertIsString(value: unknown): asserts value is string {
  if (typeof value !== "string") {
    throw new Error(`Expected string, got ${typeof value}`);
  }
}

function processInput(input: unknown) {
  assertIsString(input);
  // input is string here
  console.log(input.toUpperCase());
}
```

# TypeScript Utility Types


## Parameters<T>

Extracts the parameter types of a function type as a tuple:

```typescript
function fetchUser(id: string, opts?: { timeout?: number }): Promise<User> {
  // ...
}

type FetchUserParams = Parameters<typeof fetchUser>;
// Type: [id: string, opts?: { timeout?: number } | undefined]

// Use in wrapper functions
const fetchUserWithLogging = async (
  ...args: Parameters<typeof fetchUser>
): Promise<User> => {
  console.log("Fetching user:", args[0]);
  return fetchUser(...args);
};
```

## ReturnType<T>

Extracts the return type of a function type:

```typescript
function createUser(name: string, email: string) {
  return {
    id: crypto.randomUUID(),
    name,
    email,
    createdAt: new Date(),
  };
}

type User = ReturnType<typeof createUser>;
// Type: { id: string; name: string; email: string; createdAt: Date }
```

## Awaited<T>

Unwraps the type inside a Promise (including nested Promises):

```typescript
type PromiseString = Promise<string>;
type NestedPromise = Promise<Promise<number>>;

type Unwrapped1 = Awaited<PromiseString>; // string
type Unwrapped2 = Awaited<NestedPromise>; // number

// Combine with ReturnType for async functions
async function fetchUser(id: string): Promise<User> {
  // ...
}

type FetchUserResult = Awaited<ReturnType<typeof fetchUser>>;
// Type: User (not Promise<User>)
```

## Pattern: Wrapping External Library Functions

When extending functions from external libraries that don't export their types:

```typescript
import { fetchUser } from "external-lib";

// Extract and extend the return type
type FetchUserReturn = Awaited<ReturnType<typeof fetchUser>>;

export const fetchUserWithFullName = async (
  ...args: Parameters<typeof fetchUser>
): Promise<FetchUserReturn & { fullName: string }> => {
  const user = await fetchUser(...args);
  return {
    ...user,
    fullName: `${user.firstName} ${user.lastName}`,
  };
};
```

## Record<Keys, Type>

Creates an object type with specified keys and value type:

```typescript
type Role = "admin" | "user" | "guest";
type Permissions = Record<Role, string[]>;

const rolePermissions: Permissions = {
  admin: ["read", "write", "delete"],
  user: ["read", "write"],
  guest: ["read"],
};

// Dynamic keys with constraint
function createLookup<K extends string, V>(
  keys: K[],
  getValue: (key: K) => V
): Record<K, V> {
  const result = {} as Record<K, V>;
  for (const key of keys) {
    result[key] = getValue(key);
  }
  return result;
}
```

## Partial<T>

Makes all properties optional:

```typescript
interface User {
  id: string;
  name: string;
  email: string;
}

type UpdateUserInput = Partial<User>;
// Type: { id?: string; name?: string; email?: string }

function updateUser(id: string, updates: Partial<User>): User {
  // ...
}

updateUser("123", { name: "New Name" }); // OK - only updating name
```

## Required<T>

Makes all properties required (opposite of Partial):

```typescript
interface Config {
  host?: string;
  port?: number;
  debug?: boolean;
}

type RequiredConfig = Required<Config>;
// Type: { host: string; port: number; debug: boolean }
```

## Omit<T, Keys>

Creates a type by omitting specified properties:

```typescript
interface User {
  id: string;
  name: string;
  email: string;
  password: string;
}

type PublicUser = Omit<User, "password">;
// Type: { id: string; name: string; email: string }

type CreateUserInput = Omit<User, "id">;
// Type: { name: string; email: string; password: string }
```

## Pick<T, Keys>

Creates a type by picking specified properties (opposite of Omit):

```typescript
interface User {
  id: string;
  name: string;
  email: string;
  password: string;
  createdAt: Date;
}

type UserCredentials = Pick<User, "email" | "password">;
// Type: { email: string; password: string }
```

## Exclude<T, U> and Extract<T, U>

Work with union types:

```typescript
type AllColors = "red" | "green" | "blue" | "yellow";

type PrimaryColors = Extract<AllColors, "red" | "blue">;
// Type: "red" | "blue"

type NonPrimaryColors = Exclude<AllColors, "red" | "blue">;
// Type: "green" | "yellow"
```

## NonNullable<T>

Removes null and undefined from a type:

```typescript
type MaybeString = string | null | undefined;
type DefiniteString = NonNullable<MaybeString>;
// Type: string
```

## Creating a Reusable Wrapper Type

Combine utilities to create reusable type helpers:

```typescript
// A type that wraps any async function, extending its return type
type WrapFunction<
  TFunc extends (...args: any) => any,
  TAdditional = {}
> = (
  ...args: Parameters<TFunc>
) => Promise<Awaited<ReturnType<TFunc>> & TAdditional>;

// Usage
import { fetchUser, fetchPost } from "external-lib";

const fetchUserWithMeta: WrapFunction<
  typeof fetchUser,
  { meta: { fetchedAt: Date } }
> = async (...args) => {
  const user = await fetchUser(...args);
  return {
    ...user,
    meta: { fetchedAt: new Date() },
  };
};
```

## When to Use Each Utility

| Utility | Use Case |
|---------|----------|
| `Parameters<T>` | Wrapping functions, creating function variants |
| `ReturnType<T>` | Extracting return types when not explicitly exported |
| `Awaited<T>` | Unwrapping Promise types |
| `Record<K, V>` | Creating object types with dynamic keys |
| `Partial<T>` | Update/patch operations |
| `Required<T>` | Ensuring all config options are provided |
| `Omit<T, K>` | Removing sensitive or internal fields |
| `Pick<T, K>` | Creating focused subsets of types |
| `Exclude<T, U>` | Filtering union types |
| `Extract<T, U>` | Selecting from union types |
| `NonNullable<T>` | Removing null/undefined after validation |

## Common Pitfalls

### Using ReturnType on Async Functions

```typescript
async function getData(): Promise<string[]> {
  return ["data"];
}

// This gives Promise<string[]>, not string[]
type Wrong = ReturnType<typeof getData>; // Promise<string[]>

// Use Awaited to unwrap
type Right = Awaited<ReturnType<typeof getData>>; // string[]
```

### Forgetting typeof for Runtime Functions

```typescript
function myFunc(x: number): string {
  return String(x);
}

// Wrong - myFunc is a value, not a type
type Params = Parameters<myFunc>; // Error

// Correct - use typeof
type Params = Parameters<typeof myFunc>; // [x: number]
```