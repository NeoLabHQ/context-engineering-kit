# git-notes - Commit Metadata Annotations

Use when adding metadata to commits without changing history, tracking review status, test results, code quality annotations, or supplementing commit messages post-hoc.

- Purpose - Attach non-invasive metadata to Git objects without modifying commit history
- Core Principle - Add information to commits after creation without rewriting history

**Key Concepts**

| Concept | Description |
|---------|-------------|
| Notes ref | Storage location, default `refs/notes/commits` |
| Non-invasive | Notes never modify SHA of original object |
| Namespaces | Use `--ref` for different note categories (reviews, testing, audit) |
| Display | Notes appear in `git log` and `git show` output |

**Quick Reference**

| Task | Command |
|------|---------|
| Add note | `git notes add -m "message" <sha>` |
| View note | `git notes show <sha>` |
| Append to note | `git notes append -m "message" <sha>` |
| Use namespace | `git notes --ref=<name> <command>` |
| Push notes | `git push origin refs/notes/<name>` |

**Common Use Cases**

- **Code Review Tracking** - Mark commits as reviewed with reviewer attribution
- **Test Results Annotation** - Record test pass/fail status and coverage
- **Audit Trail** - Attach security review or compliance information
- **Sharing Notes** - Push/fetch notes to share metadata with team
