# Plugin management commands

plugins := "code-review customaize-agent ddd docs git kaizen mcp reflexion sadd sdd tdd tech-stack fpf"
marketplace := ".claude-plugin/marketplace.json"

# Show all commands
help:
    @just --list

# Copy README.md files from docs/plugins/ to respective plugins/ folders
sync-docs-to-plugins:
    @echo "Syncing README.md files from docs/plugins/ to plugins/..."
    @for plugin in {{plugins}}; do \
        if [ -f "docs/plugins/$plugin/README.md" ]; then \
            cp "docs/plugins/$plugin/README.md" "plugins/$plugin/README.md"; \
            echo "  Copied: docs/plugins/$plugin/README.md -> plugins/$plugin/README.md"; \
        else \
            echo "  Skipped: docs/plugins/$plugin/README.md (not found)"; \
        fi; \
    done
    @echo "Done."

# Copy README.md files from plugins/ to docs/plugins/ folders
sync-plugins-to-docs:
    @echo "Syncing README.md files from plugins/ to docs/plugins/..."
    @for plugin in {{plugins}}; do \
        if [ -f "plugins/$plugin/README.md" ]; then \
            mkdir -p "docs/plugins/$plugin"; \
            cp "plugins/$plugin/README.md" "docs/plugins/$plugin/README.md"; \
            echo "  Copied: plugins/$plugin/README.md -> docs/plugins/$plugin/README.md"; \
        else \
            echo "  Skipped: plugins/$plugin/README.md (not found)"; \
        fi; \
    done
    @echo "Done."

# Set version for a specific plugin
set-version plugin version:
    @if [ ! -f "plugins/{{plugin}}/.claude-plugin/plugin.json" ]; then \
        echo "Error: Plugin '{{plugin}}' not found"; \
        exit 1; \
    fi
    @echo "Updating version for plugin '{{plugin}}' to {{version}}..."
    @# Update plugin.json
    @jq '.version = "{{version}}"' "plugins/{{plugin}}/.claude-plugin/plugin.json" > "plugins/{{plugin}}/.claude-plugin/plugin.json.tmp" && \
        mv "plugins/{{plugin}}/.claude-plugin/plugin.json.tmp" "plugins/{{plugin}}/.claude-plugin/plugin.json"
    @echo "  Updated: plugins/{{plugin}}/.claude-plugin/plugin.json"
    @# Update marketplace.json
    @jq '(.plugins[] | select(.name == "{{plugin}}")).version = "{{version}}"' "{{marketplace}}" > "{{marketplace}}.tmp" && \
        mv "{{marketplace}}.tmp" "{{marketplace}}"
    @echo "  Updated: {{marketplace}}"
    @echo "Done. Version set to {{version}} for plugin '{{plugin}}'"

# Set version for the marketplace
set-marketplace-version version:
    @if [ ! -f "{{marketplace}}" ]; then \
        echo "Error: Marketplace file '{{marketplace}}' not found"; \
        exit 1; \
    fi
    @echo "Updating marketplace version to {{version}}..."
    @jq '.version = "{{version}}"' "{{marketplace}}" > "{{marketplace}}.tmp" && \
        mv "{{marketplace}}.tmp" "{{marketplace}}"
    @echo "  Updated: {{marketplace}}"
    @echo "Done. Marketplace version set to {{version}}"

# List all available plugins
list-plugins:
    @echo "Available plugins:"
    @for plugin in {{plugins}}; do \
        if [ -f "plugins/$plugin/.claude-plugin/plugin.json" ]; then \
            version=$(jq -r '.version' "plugins/$plugin/.claude-plugin/plugin.json"); \
            echo "  $plugin (v$version)"; \
        fi; \
    done
