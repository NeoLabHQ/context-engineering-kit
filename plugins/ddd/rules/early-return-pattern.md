---
title: Use Early Returns to Reduce Nesting
impact: MEDIUM
paths:
  - "**/*"
  - "**/*"
---

# Use Early Returns to Reduce Nesting

Always use early returns to handle error conditions and edge cases at the top of functions instead of wrapping logic in nested conditionals. Deeply nested code (more than 3 levels) increases cognitive load, obscures the happy path, and makes functions harder to read, review, and maintain. When guard clauses are placed first, the main logic stays at the top indentation level and reads linearly from top to bottom.

## Incorrect

Validation checks are nested inside each other, pushing the core business logic deep into indentation. The happy path is buried at the innermost level, and error handling is scattered across multiple `else` branches at the bottom.

```typescript
async function validateUser(userId: string, role: string): Promise<User> {
  if (userId) {
    const user = await db.users.findById(userId)
    if (user) {
      if (!user.isDeleted) {
        if (user.role === role) {
          if (user.emailVerified) {
            // happy path buried 5 levels deep
            return user
          } else {
            throw new Error('Email not verified')
          }
        } else {
          throw new Error('Insufficient role')
        }
      } else {
        throw new Error('User is deleted')
      }
    } else {
      throw new Error('User not found')
    }
  } else {
    throw new Error('User ID is required')
  }
}
```

## Correct

Guard clauses handle each error condition with an early return at the top level. The happy path flows naturally at the end of the function with zero unnecessary nesting.

```typescript
async function validateUser(userId: string, role: string): Promise<User> {
  if (!userId)
    throw new Error('User ID is required')

  const user = await db.users.findById(userId)
  if (!user)
    throw new Error('User not found')
  if (user.isDeleted)
    throw new Error('User is deleted')
  if (user.role !== role)
    throw new Error('Insufficient role')
  if (!user.emailVerified)
    throw new Error('Email not verified')

  return user
}
```

## Reference

- [Flattening Arrow Code](https://blog.codinghorror.com/flattening-arrow-code/)
