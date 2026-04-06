---
title: Principle of Least Astonishment — Functions Must Do Only What Their Name Promises
paths:
  - "src/**/*"
impact: HIGH
---

# Principle of Least Astonishment — Functions Must Do Only What Their Name Promises

A function must do exactly what its name and signature suggest — nothing more, nothing less. Hidden side effects violate caller expectations, create invisible coupling, and make code unpredictable. When a function named `getUser` also emits analytics events, or a function named `validate` throws instead of returning a boolean, callers cannot reason about behavior from the interface alone. This forces every developer to read the implementation before using the function, defeating the purpose of abstraction.

Keep functions honest: if a name implies a pure query, do not mutate state. If a name implies validation, return a result rather than throwing. Make all side effects explicit at the call site so the reader's mental model matches the actual execution. When additional work is needed (logging, analytics, notifications), perform it in the calling code or use clearly named wrapper functions that advertise the combined behavior.

## Incorrect

The function name `getUser` promises a data retrieval operation, but it secretly logs an analytics event and updates a last-accessed timestamp — side effects the caller never asked for and cannot see from the signature.

```typescript
// user-service.ts — hidden side effects inside a getter
async function getUser(userId: string): Promise<User> {
  const user = await userRepository.findById(userId);
  if (!user) throw new NotFoundError("User not found");

  // Hidden side effect: analytics tracking
  await analyticsService.track("user_viewed", {
    userId: user.id,
    timestamp: new Date().toISOString(),
  });

  // Hidden side effect: mutates database state
  await userRepository.updateLastAccessed(userId, new Date());

  return user;
}
```

## Correct

The getter does only what its name says — retrieves a user. Side effects are performed explicitly at the call site, where the caller can see and control them.

```typescript
// user-service.ts — getter does only what the name promises
async function getUser(userId: string): Promise<User> {
  const user = await userRepository.findById(userId);
  if (!user) throw new NotFoundError("User not found");
  return user;
}

// call site — side effects are explicit and visible
const user = await getUser(userId);
await analyticsService.track("user_viewed", { userId: user.id });
await userRepository.updateLastAccessed(userId, new Date());
```

## Reference

- [Principle of Least Astonishment (Wikipedia)](https://en.wikipedia.org/wiki/Principle_of_least_astonishment)
- [Clean Code by Robert C. Martin](https://www.oreilly.com/library/view/clean-code-a/9780136083238/) — Chapter 3: Functions should do one thing
