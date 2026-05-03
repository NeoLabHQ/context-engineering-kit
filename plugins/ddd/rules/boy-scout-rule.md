---
title: Boy Scout Rule — Incremental Improvement Without Scope Creep
paths:
  - "src/**/*"
---

# Boy Scout Rule — Incremental Improvement Without Scope Creep

Rules: 
- Leave code better than you found it (Martin, "Clean Code") — but limit improvements to the code you are already touching. 
- Apply Opportunistic Refactoring (Fowler): make small cleanups while working on a task, not as a separate effort. Stop when the improvement is unrelated to your current change. 
- Over-engineering disguised as "cleaning up" violates YAGNI (Beck & Jeffries, "Extreme Programming") and expands scope, making changes harder to review, test, and revert.

**Appropriate improvements** when touching a function: rename unclear variables, add missing type annotations, extract a small helper, remove dead code, fix an obvious code smell.

**Not appropriate** when fixing a bug or adding a feature: restructuring entire modules, introducing new design patterns, refactoring code in files you are not otherwise modifying, replacing working implementations with "better" alternatives.


## Example

Task is to fix a null-check bug in `getUser`. Agent also restructures the module, renames unrelated functions, and introduces a new pattern — turning a one-line fix into a large, unrelated refactor.

### Before

Starting code: `getUser` can crash when `user.profile` is missing

```typescript
// Task: fix bug — getUser crashes when user has no profile

import { userRepo } from './userRepo';
import { formatName } from './formatName';

export async function getUser(id: string): Promise<User> {
  const user = await userRepo.findById(id);
  if (!user) {
    throw new NotFoundError('User');
  }
  // Bug: assumes profile always exists
  const r = { ...user, displayName: formatName(user.name, user.profile) };
  return r;
}
```

### Incorrect

Agent rewrites the whole module instead of fixing the bug in place.

```typescript
// Task: fix bug — getUser crashes when user has no profile

// Agent rewrites entire module instead of fixing the bug
import { pipe } from 'fp-ts/function';
import * as O from 'fp-ts/Option';

// Renamed from getUser to fetchUserWithProfile (unrelated change)
export async function fetchUserWithProfile(id: string): Promise<UserDTO> {
  // Introduced Result pattern (unrelated change)
  const result = await pipe(
    userRepo.findById(id),
    O.fromNullable,
    O.map(enrichWithProfile),
    O.getOrElse(() => { throw new NotFoundError('User'); })
  );
  // Extracted new DTO mapper (unrelated change)
  return UserMapper.toDTO(result);
}

// Refactored other functions not related to the bug
export async function listUsers(): Promise<UserDTO[]> { /* ... rewritten ... */ }
export async function deleteUser(id: string): Promise<void> { /* ... rewritten ... */ }
```

### Correct

Agent fixes the bug and makes only small, adjacent improvements to the code it already touches.

```typescript
// Task: fix bug — getUser crashes when user has no profile
export async function getUser(id: string): Promise<User> {
  const user = await userRepo.findById(id);
  if (!user) {
    throw new NotFoundError('User');
  }

  // Bug fix: guard against missing profile
  const profile = user.profile ?? DEFAULT_PROFILE;

  // Boy scout: remove unclear variable that only makes the code more complex
  return { ...user, profile, displayName: formatName(user.name) };
}
```

## Reference

- [Clean Code — Robert C. Martin](https://www.oreilly.com/library/view/clean-code/9780136083238/) — Boy Scout Rule: "Leave the campground cleaner than you found it"
- [Opportunistic Refactoring — Martin Fowler](https://martinfowler.com/bliki/OpportunisticRefactoring.html) — "Refactor as you go, not as a separate activity"
- [Extreme Programming Explained — Kent Beck & Ron Jeffries](https://www.oreilly.com/library/view/extreme-programming-explained/0201616416/) — YAGNI: "You Aren't Gonna Need It"
