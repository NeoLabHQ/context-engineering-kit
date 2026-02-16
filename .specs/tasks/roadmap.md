
# Roadmap for V2 release

## Tasks

[x] Move all commands to skills format, in order to properly support all installers
[] Add support for vercel skill installer - but left support for installers that exists now
[] Publish skills in vercel marketplace
[] Add skills to https://github.com/VoltAgent/awesome-agent-skills
[x] Migrate SDD plugin to v2 version
    [x] Fix issues with scratchpad id generation - potentially write script for generation of them
    [x] switch to `git mv` instead of `mv` in order to keep git history clean and avoid conflicts.
    [x] Write a script that create folder setup and adds scratchpad folder to gitignore
    [x] Add support for flags of `/implementaion` command that allow to increase and decreate amount of guality, amount of iterations allowed, `--human-in-the-loop` flag to allow to pause for human verification after each step and `--refine` flag that will perform refinement of implementation after human feedback or corrections. Need check whether it have `--continue` flag, it not then add it.
    [x] Increase amount of maximum iteration to 3 for planing and 3-4 for implementation phase -> Decided to keep iterations unlimited for now.
[x] Update project readme with new features and changes. Remove majoirty of content and move it to docs/, also verify with another projects on best practices of readme. And update header image to be transparent.

## In consideration for V2.1

SDD plugin:
    [] potentially add plan-directly command that allow to plan without using subagents

## In consideration for V3

Possible to create `workflow.yaml` file that will be used to define local pipeline for code development with quality gates and LLM-as-Judge verification. Main focus should be on quality gates they can include:

- Tests with plugin for minimal code coverage and mutation testing. For example if tests not pass 80% coverage it should be returned to coding agent with comment: "Tests coverage is not enough. Please increase coverage to 80% or higher. If writing tests for this code is to complicated, consider refactoring it for better testability and using dependency injection pattern."
- Linting with default integrations with eslint, prettier, tslint, etc. That marks all warninigs as errors, tryies to autofix them and if it fails ask agent to do it.
- Build or compilation test using npm build, tsc, docker build, bun build, etc. With potentially marking warnings as errors and trying to autofix them.
- Security audit using tools like npm audit, tslint audit, etc. With potentially marking warnings as errors and trying to autofix them.
- Code quality search as ast-grep, jscpd, super-linter and MegaLinter (it designed as github action that supports almost all linters for all frameworks, but will be good to use it as code quality check locally), etc.
- Static code analysis using tools like SonarQube, CodeFactor, Codacy, etc. Need check which of them free (Codacy looks like that) and enable it by default
- Dependency and dead code analysis using tools like knip, depcheck, etc.
- Code complexity analysis using tools like cloc/scc (define maximum allowed lines of code per file, per function, per class), or other code complexity metrics. (Mental complexity, cyclomatic complexity, etc.)
- Human-in-the-loop verification after each or specific steps of the process.

[] Possible to add ast-grep support for code-base impact analysis step. Or even as mcp toof for all agents. Or as part of code quality workflow. It allow to search, lint and rewrite code. And allow to write liniting rules using yaml!
[] jscpd allow to detected code dublication and support 150 languages.

