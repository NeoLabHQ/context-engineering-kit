# Quality Agent Marketplace

Hand-crafted production ready Claude Code plugin marketplace focused on improving agent result quality.

**Philosophy:** Easy to install and use, with minimal token footprint.

## Features

- **Simple to Use** - Easy to install and use without any dependencies. Contain automatically used skills and self-explanatory commands.
- **Token-Efficient** - Carefully crafted prompts and architecture, prefering commands over skills, to minimize populating context with unnecessary information.
- **Quality-Focused** - Each plugin focused on meaningfully improving agent result over specific area. Developoed by experienced developers that need to get relaible results on production code.
- **Granular** - Install only the plugins you need. Each plugin loads only its specific agents, commands, and skills.
- **Well-targeted** - Marketplace contains minimal amount of plugins, without overlap and redundant skills. It is based on prompts that used by our company developers daily for long time, with combained plugins from high quality projects. If you looking for more general plugins, take a loog at [Based on section](#based-on)

## Quick Start

Browse available plugins in [PLUGINS.md](PLUGINS.md)

### Install a Plugin

```bash
cd ~/.claude-code/plugins/
git clone https://github.com/neolab/quality-agent.git
ln -s quality-agent/plugins/code-quality/code-review-checklist ./
```

Then use it in Claude Code:

```
/review-checklist
```

## Plugin Categories

- **Code Quality** - Reviews, linting, style checks
- **Testing** - Test generation, coverage, validation
- **Documentation** - Docs generation, maintenance

## Contributing

We welcome high-quality plugin contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Based on <a name="based-on"></a>

This project improves plugins collected across multiple projects and marketplaces.

List of main sources:

- [Official Claude Code plugins](https://github.com/anthropics/claude-code/tree/main/plugins)
- [Claude Task Master](https://github.com/eyaltoledano/claude-task-master)
- [Multi-agent Orchestration](https://github.com/wshobson/agents)
- [Anthropic example skills](https://github.com/anthropics/skills)
- [Claude Flow](https://github.com/ruvnet/claude-flow)
- [Superpowers](https://github.com/obra/superpowers/tree/main)
- [Awesome Claude Skills](https://github.com/ComposioHQ/awesome-claude-skills)
- [Beads](https://github.com/steveyegge/beads)

## Recomendend MCP Servers

Servers recommended for use with this marketplace:

- [Context7](https://github.com/upstash/context7)
- [Serena](https://github.com/oraios/serena)
- [Perplexity Model Context Protocol](https://github.com/perplexityai/modelcontextprotocol)
