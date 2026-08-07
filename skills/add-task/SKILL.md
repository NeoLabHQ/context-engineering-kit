---
name: add-task
description: creates draft task file in .specs/tasks/draft/ with original user intent
argument-hint: Task title or description (e.g., "Add validation to form inputs") [list of task files that this task depends on]
---

# Create Draft Task File

## Role

Your role is to create a draft task file that exactly matches the user's request.

## Goal

Create a task file in `.specs/tasks/draft/` with:

- Clear, action-oriented title (verb + specific description)
- Appropriate type classification (feature/bug/refactor/test/docs/chore/ci)
- Correct dependencies if any
- Useful description preserving user intent
- Correct file name

## Input

- **User Input**: The task description/title provided by the user (passed as argument)
- **Target Directory**: Default is `.specs/tasks/draft/`

## Instructions

### 1. Ensure Directory Structure

Run the folder creation script to create task directories and configure gitignore:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/create-folders.sh
```

This creates:

- `.specs/tasks/draft/` - New tasks awaiting analysis
- `.specs/tasks/todo/` - Tasks ready to implement
- `.specs/tasks/in-progress/` - Currently being worked on
- `.specs/tasks/done/` - Completed tasks
- `.specs/scratchpad/` - Temporary working files (gitignored)

### 2. Analyze Input

1. **Parse the user's request**:
   - Extract the core task objective
   - Identify implied type (bug, feature, task)
   - List of task files that this task depends on

2. **Clarify if ambiguous** (only if truly unclear):
   - Is this a bug fix or new feature?
   - Any related tasks or dependencies? (if not proided, then assume none)

### 3. Structure the Task

1. **Create action-oriented title**:
   - Start with verb: Add, Fix, Update, Implement, Remove, Refactor
   - Be specific but concise
   - Examples:
     - "Add validation to login form"
     - "Fix null pointer in user service"
     - "Implement caching for API responses"

2. **Determine type**:

   | Type | Use When |
   |------|----------|
   | `feature` | New functionality or capability |
   | `bug` | Something is broken or not working correctly |
   | `refactor` | Code restructuring without changing behavior |
   | `test` | Adding or updating tests |
   | `docs` | Documentation changes only |
   | `chore` | Maintenance tasks, dependency updates |
   | `ci` | CI/CD configuration changes |

### 4. Generate File Name

1. **Create short name from the task title**:
   - Lowercase the title
   - Replace spaces with hyphens
   - Remove special characters
   - Keep it concise (3-5 words max)
   - Example: "Add validation to login form" -> `add-validation-login-form`

2. **Form file name**: `<short-name>.<issue-type>.md`
   - Examples:
     - `add-validation-login-form.feature.md`
     - `fix-null-pointer-user-service.bug.md`
     - `restructure-auth-module.refactor.md`
     - `add-unit-tests-api.test.md`
     - `update-readme.docs.md`
     - `upgrade-dependencies.chore.md`
     - `add-github-actions.ci.md`

3. **Verify uniqueness**: Check `.specs/tasks/draft/`, `.specs/tasks/todo/`, `.specs/tasks/in-progress/`, and `.specs/tasks/done/` for existing files with same name

### 5. Create Task File

**Use Write tool** to create `.specs/tasks/todo/<short-name>.<issue-type>.md`:

```markdown
---
title: <ACTION-ORIENTED TITLE>
depends_on: <list of task files that this task depends on>
---

## Initial User Prompt

{EXACT user input as provided}

## Description

// Will be filled in future stages by business analyst
```

## Constraints

- **Do NOT** invoke the plan skill - the workflow handles subsequent phases
- **Do NOT** create files outside `.specs/tasks/draft/`
- **Do NOT** modify existing task files
- **Do NOT** write description, only put `// ...` placeholder as specified in the task file.
- **Do NOT** write depends_on section if no dependencies are provided.

## Expected Output

Return to the orchestrator:

1. **Task file path**: Full path to created file (e.g., `.specs/tasks/todo/add-validation-login-form.feature.md`)
2. **Generated title**: The action-oriented title created
3. **Issue type**: `task`, `bug`, or `feature`

Format:

```
Created task file: .specs/tasks/draft/<name>.<type>.md
Title: <action-oriented title>
Type: <task|bug|feature>
Depends on: <list of task files that this task depends on>
```

## Success Criteria

- [ ] Directories `.specs/tasks/draft/`, `.specs/tasks/todo/`, `.specs/tasks/in-progress/`, `.specs/tasks/done/` exist
- [ ] Task file created in `.specs/tasks/draft/` with correct naming convention (`<name>.<type>.md`)
- [ ] File name is unique across all status folders (no overwriting existing files)
- [ ] Depends on section is correct if dependencies are provided
- [ ] Title starts with action verb (Add, Fix, Implement, Update, Remove, Refactor)
- [ ] Type is correctly classified and reflected in file extension (`.feature.md`, `.bug.md`, `.refactor.md`, `.test.md`, `.docs.md`, `.chore.md`, `.ci.md`)
- [ ] Original user input preserved in "Initial User Prompt" section
- [ ] Description is empty placeholder `// Will be filled in future stages by business analyst`

## Examples

**Test task** (`.specs/tasks/draft/add-unit-tests-auth.test.md`):

```markdown
---
title: Add unit tests for auth module
---

## Initial User Prompt

add tests for auth

## Description

// Will be filled in future stages by business analyst
```

**Bug with context** (`.specs/tasks/draft/fix-login-timeout.bug.md`):

```markdown
---
title: Fix login timeout on slow connections
---

## Initial User Prompt

users getting 504 errors on slow wifi

## Description

// Will be filled in future stages by business analyst
```

**Feature request** (`.specs/tasks/draft/implement-dark-mode.feature.md`):

```markdown
---
title: Implement dark mode toggle
---

## Initial User Prompt

add dark mode to settings page

## Description

// Will be filled in future stages by business analyst
```
