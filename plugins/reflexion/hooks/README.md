# Reflexion Hooks

Claude Code hooks for automatic reflection triggering. When the word "reflect" appears in a user prompt, the hook intercepts Claude's stop signal and automatically executes the `/reflexion:reflect` command.

## How It Works

### Architecture Overview

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  UserPromptSubmit   │───▶│    Session Store     │───▶│    Stop Handler     │
│      (record)       │    │   (temp JSON file)   │    │   (check & block)   │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                                                 │
                                                                 ▼
                                                       ┌─────────────────────┐
                                                       │  "reflect" found?   │
                                                       │  No consecutive     │
                                                       │  Stop calls?        │
                                                       └─────────────────────┘
                                                                 │
                                                           YES   │   NO
                                                           ┌─────┴─────┐
                                                           ▼           ▼
                                                  Block & trigger   Continue
                                                  /reflexion:reflect
```

### Flow

1. **UserPromptSubmit Hook**: Records every user prompt in session storage
2. **Stop Hook**: When Claude finishes, checks if "reflect" was in the last user prompt
3. **Cycle Prevention**: Ensures no consecutive Stop calls (prevents infinite loops)
4. **Trigger**: If conditions met, blocks stop and instructs Claude to run `/reflexion:reflect`

### Key Components

| File | Purpose |
|------|---------|
| `hooks.json` | Hook configuration - registers Stop and UserPromptSubmit events |
| `src/index.ts` | Entry point - registers all handlers |
| `src/onStopHandler.ts` | Stop handler with reflection trigger logic |
| `src/session.ts` | Session persistence for tracking hook invocations |
| `src/lib.ts` | Types, payload interfaces, and hook infrastructure |

### Trigger Logic (onStopHandler.ts)

```typescript
// Trigger word detection with word boundaries
const TRIGGER_WORD = "reflect"
// Uses regex \b to match whole word only - won't match "reflection" or "reflective"

// Cycle prevention
// Filters session to only UserPromptSubmit and Stop hooks
// Checks that last hook was UserPromptSubmit, not another Stop
// This prevents: Stop → Block → Stop → Block → ... infinite loop
```

### Session Data

Hook invocations are persisted to temp files (`/tmp/claude-hooks-sessions/<session_id>.json`) allowing the Stop handler to access the original user prompt even though it's not in the Stop payload.

## Installation

```bash
cd plugins/reflexion/hooks
bun install
```

## Usage

### Start Claude Code with the plugin

```bash
# With debug output (shows sessionData in hook responses)
DEBUG=true claude --debug --plugin-dir ./plugins/reflexion

# Normal mode
claude --plugin-dir ./plugins/reflexion
```

### Trigger Reflection

Simply include the word "reflect" in your prompt:

```
> Fix the bug in auth.ts then reflect
# Claude fixes the bug, then automatically runs /reflexion:reflect

> Implement the feature, reflect on your work
# Same behavior - "reflect" triggers automatic reflection
```

**Note**: Only the exact word "reflect" triggers this behavior. Words like "reflection", "reflective", or "reflects" will not trigger it.

### Debug Mode

When running with `DEBUG=true`, hook responses include the full session data for debugging:

```json
{
  "decision": "block",
  "reason": "You MUST use Skill tool to execute the command /reflexion:reflect",
  "sessionData": [
    {"timestamp": "...", "hookType": "UserPromptSubmit", "payload": {...}},
    {"timestamp": "...", "hookType": "Stop", "payload": {...}}
  ]
}
```

## Development

### Project Structure

```
hooks/
├── src/
│   ├── index.ts              # Entry point, registers handlers
│   ├── onStopHandler.ts      # Stop handler with trigger logic
│   ├── onStopHandler.test.ts # Tests for stop handler
│   ├── session.ts            # Session data persistence
│   └── lib.ts                # Types and hook infrastructure
├── hooks.json                # Hook event configuration
├── package.json
├── tsconfig.json
└── vitest.config.ts
```

### Running Locally

```bash
bun run src/index.ts Stop          # Test stop handler
bun run src/index.ts UserPromptSubmit  # Test prompt handler
```

### Testing

Uses Vitest for testing. Run with npm (vitest has issues with bun):

```bash
npm test
```

### Extending

To add new hook handlers:

1. Create handler in `src/` following `onStopHandler.ts` pattern
2. Register in `src/index.ts` handlers object
3. Add hook event to `hooks.json` if not already configured

### Available Hook Types

| Hook | When Called | Can Block |
|------|-------------|-----------|
| `SessionStart` | New Claude session starts | Yes |
| `UserPromptSubmit` | User submits a prompt | Yes |
| `PreToolUse` | Before Claude uses a tool | Yes (deny) |
| `PostToolUse` | After Claude uses a tool | Yes |
| `Stop` | Claude finishes responding | Yes |
| `SubagentStop` | Subagent (Task tool) finishes | Yes |
| `PreCompact` | Before conversation compaction | Yes |
| `Notification` | Claude sends notification | No |

## Troubleshooting

### Hook not triggering

1. Ensure bun is installed: `bun --version`
2. Check hooks.json is valid JSON
3. Run with DEBUG=true to see hook output
4. Verify "reflect" is a standalone word (not part of another word)

### Infinite loop detected

The handler has built-in cycle prevention. If you see "Detected consecutive STOP invocations", it means the handler correctly prevented a loop.

### Session data not found

Session files are stored in `/tmp/claude-hooks-sessions/`. If missing, ensure the hooks directory has write permissions to temp.
