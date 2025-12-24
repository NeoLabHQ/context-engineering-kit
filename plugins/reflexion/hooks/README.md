# hooks

To install dependencies:

```bash
bun install
```

To run:

```bash
bun run index.ts
```

This project was created using `bun init` in bun v1.0.3. [Bun](https://bun.sh) is a fast all-in-one JavaScript runtime.

## Testing

For testing use npm, vitest not work properly with bun.

```bash
npm test
```

### Start claude code with plugin

```bash
DEBUG=true claude --debug --plugin-dir ./plugins/reflexion
```
