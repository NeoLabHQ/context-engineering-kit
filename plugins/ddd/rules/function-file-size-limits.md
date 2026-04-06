---
title: Function and File Size Limits
impact: MEDIUM
paths:
  - "**/*"
  - "**/*"
---

# Function and File Size Limits

- Decompose functions longer than 80 lines into smaller, focused functions of 50 lines or fewer. When a function grows beyond 80 lines, it is almost certainly doing more than one thing and should be split. 
- Keep files under 200 lines of code. Large functions accumulate multiple responsibilities, making them harder to test, review, and reuse. 
- Extract cohesive blocks of logic into named functions that each serve a single purpose. If extracted functions are only used within the same context, keep them in the same file. However, when a file exceeds 200 lines even after decomposition, split related functions into separate modules grouped by responsibility.

## Incorrect

A single function handles validation, transformation, persistence, and notification. At over 80 lines it is difficult to test individual behaviors or reuse any part of the logic.

```typescript
async function processUserRegistration(input: unknown) {
  // Validate input (lines 1-20)
  if (!input || typeof input !== 'object') throw new Error('Invalid input')
  const { email, name, password, role } = input as Record<string, unknown>
  if (!email || typeof email !== 'string') throw new Error('Email required')
  if (!name || typeof name !== 'string') throw new Error('Name required')
  if (!password || typeof password !== 'string') throw new Error('Password required')
  if (password.length < 8) throw new Error('Password too short')
  if (!/[A-Z]/.test(password)) throw new Error('Password needs uppercase')
  if (!/[0-9]/.test(password)) throw new Error('Password needs digit')
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) throw new Error('Invalid email format')

  // Normalize data (lines 21-35)
  const normalizedEmail = email.toLowerCase().trim()
  const normalizedName = name.trim().replace(/\s+/g, ' ')
  const hashedPassword = await bcrypt.hash(password, 12)
  const assignedRole = role === 'admin' ? 'user' : (role as string) || 'user'
  const createdAt = new Date()
  const updatedAt = new Date()

  // Check duplicates and persist (lines 36-55)
  const existing = await db.users.findUnique({ where: { email: normalizedEmail } })
  if (existing) throw new Error('Email already registered')
  const user = await db.users.create({
    data: {
      email: normalizedEmail,
      name: normalizedName,
      password: hashedPassword,
      role: assignedRole,
      createdAt,
      updatedAt,
    },
  })

  // Send notifications (lines 56-80+)
  const welcomeHtml = `<h1>Welcome ${normalizedName}</h1><p>Your account is ready.</p>`
  await emailService.send({
    to: normalizedEmail,
    subject: 'Welcome!',
    html: welcomeHtml,
  })
  await analyticsService.track('user_registered', {
    userId: user.id,
    role: assignedRole,
    timestamp: createdAt.toISOString(),
  })
  await auditLog.record('registration', { userId: user.id, email: normalizedEmail })

  return user
}
```

## Correct

Each responsibility is extracted into a focused function under 50 lines. Functions that are only used together stay in the same file.

```typescript
function validateRegistrationInput(input: unknown): RegistrationInput {
  if (!input || typeof input !== 'object') throw new Error('Invalid input')
  const { email, name, password, role } = input as Record<string, unknown>
  if (!email || typeof email !== 'string') throw new Error('Email required')
  if (!name || typeof name !== 'string') throw new Error('Name required')
  if (!password || typeof password !== 'string') throw new Error('Password required')
  if (password.length < 8) throw new Error('Password too short')
  if (!/[A-Z]/.test(password)) throw new Error('Password needs uppercase')
  if (!/[0-9]/.test(password)) throw new Error('Password needs digit')
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new Error('Invalid email format')
  return { email, name, password, role: typeof role === 'string' ? role : 'user' }
}

async function normalizeAndHash(input: RegistrationInput): Promise<NormalizedUser> {
  return {
    email: input.email.toLowerCase().trim(),
    name: input.name.trim().replace(/\s+/g, ' '),
    password: await bcrypt.hash(input.password, 12),
    role: input.role === 'admin' ? 'user' : input.role,
  }
}

async function persistUser(data: NormalizedUser): Promise<User> {
  const existing = await db.users.findUnique({ where: { email: data.email } })
  if (existing) throw new Error('Email already registered')
  return db.users.create({ data: { ...data, createdAt: new Date(), updatedAt: new Date() } })
}

async function notifyRegistration(user: User): Promise<void> {
  await emailService.send({ to: user.email, subject: 'Welcome!', html: `<h1>Welcome ${user.name}</h1>` })
  await analyticsService.track('user_registered', { userId: user.id, role: user.role })
  await auditLog.record('registration', { userId: user.id, email: user.email })
}

async function processUserRegistration(input: unknown): Promise<User> {
  const validated = validateRegistrationInput(input)
  const normalized = await normalizeAndHash(validated)
  const user = await persistUser(normalized)
  await notifyRegistration(user)
  return user
}
```
