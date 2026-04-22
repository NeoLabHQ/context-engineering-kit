# /root-cause-tracing - Bug Tracing Through Call Stack

Systematically traces bugs backward through the call stack to identify where invalid data or incorrect behavior originates.

- Purpose - Find the source of bugs that manifest deep in execution
- Output - Trace chain from symptom to original trigger with fix recommendation

```bash
/root-cause-tracing
```

## Arguments

None. The command works with the current bug context from your conversation.

## How It Works

1. **Observe Symptom**: Identify where the error appears (e.g., wrong file created, incorrect output)
2. **Find Immediate Cause**: Locate the code that directly causes the error
3. **Trace Upward**: Ask "what called this?" and follow the chain
4. **Track Values**: Note what values were passed at each level
5. **Find Origin**: Continue until you find where invalid data originated
6. **Add Instrumentation**: If manual tracing fails, add stack trace logging
7. **Fix at Source**: Address the root trigger, not the symptom location

### Key Principle

Never fix just where the error appears. Trace back to find the original trigger.

## Usage Examples

```bash
# After encountering a deep stack error
> /root-cause-tracing

# When debugging file creation in wrong location
> /root-cause-tracing
```

### Example Trace

```
Symptom: .git created in packages/core/ (source code)

Trace chain:
1. git init runs in process.cwd() <- empty cwd parameter
2. WorktreeManager called with empty projectDir
3. Session.create() passed empty string
4. Test accessed context.tempDir before beforeEach
5. setupCoreTest() returns { tempDir: '' } initially

Root cause: Top-level variable initialization accessing empty value
Fix: Made tempDir a getter that throws if accessed before beforeEach

Defense-in-depth added:
- Layer 1: Project.create() validates directory
- Layer 2: WorkspaceManager validates not empty
- Layer 3: NODE_ENV guard refuses git init outside tmpdir
- Layer 4: Stack trace logging before git init
```

## Best practices

- Use console.error in tests - Loggers may be suppressed in test environments
- Log before dangerous operations - Capture state before failure, not after
- Include full context - Directory, cwd, environment variables, timestamps
- Add defense-in-depth - Fix at source AND add validation at each layer
- Capture stack traces - Use `new Error().stack` for complete call chains
