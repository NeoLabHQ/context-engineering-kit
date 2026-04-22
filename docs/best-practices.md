# Tips and Best Practices

## Token Efficiency

**Install only what you need:**

```bash
# ❌ Don't install all plugins
/plugin install reflexion@NeoLabHQ/context-engineering-kit
/plugin install review@NeoLabHQ/context-engineering-kit
/plugin install sdd@NeoLabHQ/context-engineering-kit
# ... (if you won't use them all)

# ✅ Install only plugins that you expect to use
/plugin install reflexion@NeoLabHQ/context-engineering-kit  # For today's feature work
```

## Maximizing Quality

By using multiple plugins together you can maximize quality of results. For example, by combining `review`, `sdd`, `sadd`, `ddd` and `git` plugins, you can follow this workflow:

```bash
# Create task file
/add-tash "Add OAuth2 based authentication"
# Write detailed specification by following Clean Architecture from DDD plugin
/plan-task
# Write code by following DDD and SOLID principles from DDD plugin
/implement-task
# Review code by following review plugin
/review-local-changes and write found issues to review.md file
# Fix found issues
/do-in-steps fix issues from review.md file
# Commit and create PR
/create-pr
```

### Use commands tailored to task size

- Small tasks - `/do-and-judge` from `sadd` plugin
- Medium tasks - `/do-in-steps` from `sadd` plugin
- Large tasks - `/plan-task` and `/implement-task` from `sdd` plugin

### Using CLAUDE.md Effectively

**Start of session:**

```text
Read CLAUDE.md and follow its guidelines
```

**After major feature:**

```bash
# Reflect on implementation
/reflect

# Memorize key insights to CLAUDE.md
/memorize
```



