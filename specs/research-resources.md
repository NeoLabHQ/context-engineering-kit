# Research Resources

Resources that contain research that can be used to build plugins.

## List

[][YOLO Mode (You Only Look Once) automates your entire Phases workflow](https://docs.traycer.ai/tasks/yolo-mode) - Claude have `--dangerously-skip-permissions` flag to skip permissions check, so it can be used to run YOLO Mode without permissions check.
[][Agent0](https://huggingface.co/papers/2511.16043) - Unleashing Self-Evolving Agents from Zero Data via Tool-Integrated Reasoning
- <https://github.com/aiming-lab/Agent0>
[][Solving a Million-Step LLM Task with Zero Errors](https://arxiv.org/abs/2511.09030) - using `cat file | claude -p "query" --output-format` will run Query via SDK, then exit with json output. 
- Adding `--max-turns 3` will limit amount of turns to 3.
- `--json-schema '{"type":"object","properties":{...}}' "query"` will validate the output against a JSON schema.
- `--model` flag to specify the model to use.
- `--permission-mode plan` will run agent in specified permissions mode <https://code.claude.com/docs/en/iam#permission-modes>

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer. Use proactively after code changes.",
    "prompt": "You are a senior code reviewer. Focus on code quality, security, and best practices.",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  },
  "debugger": {
    "description": "Debugging specialist for errors and test failures.",
    "prompt": "You are an expert debugger. Analyze errors, identify root causes, and provide fixes."
  }
}'
```
[][Agent OS](https://buildermethods.com/agent-os) - Agent OS is a spec-driven development system that gives AI agents the structured context they need to write production-quality code.
[x][codemap](https://github.com/JordanCoin/codemap) - map codebase structure
[][Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
[][mgrep](https://github.com/mixedbread-ai/mgrep)
[x][arxhiv MCP](https://hub.docker.com/mcp/server/arxiv-mcp-server/overview)
[][Docker MCP Toolkit](https://docs.docker.com/ai/mcp-catalog-and-toolkit/toolkit/)
[][Arc42 specification template] - Research Arc42 and adapt it for use in Spec Driven Development.
[][Opus soul document](https://gist.github.com/Richard-Weiss/efe157692991535403bd7e7fb20b6695)
[][YAGNI](https://martinfowler.com/bliki/Yagni.html) - Yagni originally is an acronym that stands for “You Aren't Gonna Need It”. It is a mantra from ExtremeProgramming.
[][Extreme Programming](https://martinfowler.com/bliki/ExtremeProgramming.html)
[][Beads task traker cli](https://github.com/steveyegge/beads) - maybe better to create new cli with simplified architecture, that useses only TASKS.md file.
[][Building the 14 Key Pillars of Agentic AI](https://levelup.gitconnected.com/building-the-14-key-pillars-of-agentic-ai-229e50f65986)
[] Three of Thought and etc - Expand papers that used in reflect plugin as separate comamnds/skills/hooks
[][Building Reliable RAG Pipelines Is Still Hard In 2025](https://medium.com/aiguys/building-reliable-rag-pipelines-is-still-hard-in-2025-9ba5fd92601c)