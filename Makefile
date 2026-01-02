# Makefile for Context Engineering Kit
# Plugin management commands

PLUGINS := code-review customaize-agent ddd docs git kaizen mcp reflexion sadd sdd tdd tech-stack fpf
MARKETPLACE := .claude-plugin/marketplace.json

.PHONY: help sync-docs-to-plugins sync-plugins-to-docs set-version set-marketplace-version list-plugins

help:
	@echo "Available commands:"
	@echo "  make sync-docs-to-plugins            - Copy README.md from docs/plugins/* to plugins/*"
	@echo "  make sync-plugins-to-docs            - Copy README.md from plugins/* to docs/plugins/*"
	@echo "  make set-version PLUGIN=name VERSION=x.y.z - Set version for a plugin"
	@echo "  make set-marketplace-version VERSION=x.y.z  - Set version for marketplace"
	@echo "  make list-plugins                    - List all available plugins"

# Copy README.md files from docs/plugins/ to respective plugins/ folders
sync-docs-to-plugins:
	@echo "Syncing README.md files from docs/plugins/ to plugins/..."
	@for plugin in $(PLUGINS); do \
		if [ -f "docs/plugins/$$plugin/README.md" ]; then \
			cp "docs/plugins/$$plugin/README.md" "plugins/$$plugin/README.md"; \
			echo "  Copied: docs/plugins/$$plugin/README.md -> plugins/$$plugin/README.md"; \
		else \
			echo "  Skipped: docs/plugins/$$plugin/README.md (not found)"; \
		fi; \
	done
	@echo "Done."

# Copy README.md files from plugins/ to docs/plugins/ folders
sync-plugins-to-docs:
	@echo "Syncing README.md files from plugins/ to docs/plugins/..."
	@for plugin in $(PLUGINS); do \
		if [ -f "plugins/$$plugin/README.md" ]; then \
			mkdir -p "docs/plugins/$$plugin"; \
			cp "plugins/$$plugin/README.md" "docs/plugins/$$plugin/README.md"; \
			echo "  Copied: plugins/$$plugin/README.md -> docs/plugins/$$plugin/README.md"; \
		else \
			echo "  Skipped: plugins/$$plugin/README.md (not found)"; \
		fi; \
	done
	@echo "Done."

# Set version for a specific plugin
# Usage: make set-version PLUGIN=tdd VERSION=1.2.0
set-version:
ifndef PLUGIN
	$(error PLUGIN is required. Usage: make set-version PLUGIN=name VERSION=x.y.z)
endif
ifndef VERSION
	$(error VERSION is required. Usage: make set-version PLUGIN=name VERSION=x.y.z)
endif
	@if [ ! -f "plugins/$(PLUGIN)/.claude-plugin/plugin.json" ]; then \
		echo "Error: Plugin '$(PLUGIN)' not found"; \
		exit 1; \
	fi
	@echo "Updating version for plugin '$(PLUGIN)' to $(VERSION)..."
	@# Update plugin.json
	@jq '.version = "$(VERSION)"' "plugins/$(PLUGIN)/.claude-plugin/plugin.json" > "plugins/$(PLUGIN)/.claude-plugin/plugin.json.tmp" && \
		mv "plugins/$(PLUGIN)/.claude-plugin/plugin.json.tmp" "plugins/$(PLUGIN)/.claude-plugin/plugin.json"
	@echo "  Updated: plugins/$(PLUGIN)/.claude-plugin/plugin.json"
	@# Update marketplace.json
	@jq '(.plugins[] | select(.name == "$(PLUGIN)")).version = "$(VERSION)"' "$(MARKETPLACE)" > "$(MARKETPLACE).tmp" && \
		mv "$(MARKETPLACE).tmp" "$(MARKETPLACE)"
	@echo "  Updated: $(MARKETPLACE)"
	@echo "Done. Version set to $(VERSION) for plugin '$(PLUGIN)'"

# Set version for the marketplace
set-marketplace-version:
ifndef VERSION
	$(error VERSION is required. Usage: make set-marketplace-version VERSION=x.y.z)
endif
	@if [ ! -f "$(MARKETPLACE)" ]; then \
		echo "Error: Marketplace file '$(MARKETPLACE)' not found"; \
		exit 1; \
	fi
	@echo "Updating marketplace version to $(VERSION)..."
	@jq '.version = "$(VERSION)"' "$(MARKETPLACE)" > "$(MARKETPLACE).tmp" && \
		mv "$(MARKETPLACE).tmp" "$(MARKETPLACE)"
	@echo "  Updated: $(MARKETPLACE)"
	@echo "Done. Marketplace version set to $(VERSION)"

# List all available plugins
list-plugins:
	@echo "Available plugins:"
	@for plugin in $(PLUGINS); do \
		if [ -f "plugins/$$plugin/.claude-plugin/plugin.json" ]; then \
			version=$$(jq -r '.version' "plugins/$$plugin/.claude-plugin/plugin.json"); \
			echo "  $$plugin (v$$version)"; \
		fi; \
	done
