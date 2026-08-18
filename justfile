# Plugin management commands

plugins := "review customaize-agent ddd docs git kaizen mcp reflexion sadd sdd tdd tech-stack fpf"
marketplace := ".claude-plugin/marketplace.json"

# just's own default recipe shell is "sh -cu" (dash on this repo, which has no
# associative arrays). sync-provider-formats below needs `declare -A` to detect
# skill/agent name collisions, so the shell is upgraded to bash while keeping
# the exact same "-cu" flags — every existing sh-compatible recipe still runs
# unchanged under bash.
set shell := ["bash", "-cu"]

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

# Regenerate the root-level Gemini CLI / Antigravity CLI provider bundle (skills/, agents/, gemini-extension.json, plugin.json)
#
# Neither Gemini CLI nor Antigravity CLI has a marketplace concept - each
# `gemini extensions install`/`agy plugin install` installs exactly one
# extension/plugin from a repo root manifest. So every plugin's skills/ and
# agents/ folders are merged into one root-level bundle instead of staying
# per-plugin. Full regeneration (delete then rebuild) keeps the bundle in
# sync automatically when plugin content is added or removed.
#
# Collision check runs first and touches nothing: if it fails, the previous
# bundle is left completely intact, so a real collision never leaves skills/,
# agents/, or the manifests in a partially-rebuilt state.
sync-provider-formats:
    @echo "Syncing provider formats (Gemini CLI / Antigravity CLI) at repo root..."
    @echo "  Checking for skill/agent name collisions across plugins..."; \
    declare -A skill_owner; \
    declare -A agent_owner; \
    for plugin in {{plugins}}; do \
        if [ -d "plugins/$plugin/skills" ]; then \
            for entry in "plugins/$plugin/skills"/*; do \
                [ -e "$entry" ] || continue; \
                name=$(basename "$entry"); \
                if [ -n "${skill_owner[$name]:-}" ]; then \
                    echo "Error: skill '$name' is defined by both '${skill_owner[$name]}' and '$plugin' plugins" >&2; \
                    exit 1; \
                fi; \
                skill_owner[$name]="$plugin"; \
            done; \
        fi; \
        if [ -d "plugins/$plugin/agents" ]; then \
            for entry in "plugins/$plugin/agents"/*; do \
                [ -e "$entry" ] || continue; \
                name=$(basename "$entry"); \
                if [ -n "${agent_owner[$name]:-}" ]; then \
                    echo "Error: agent '$name' is defined by both '${agent_owner[$name]}' and '$plugin' plugins" >&2; \
                    exit 1; \
                fi; \
                agent_owner[$name]="$plugin"; \
            done; \
        fi; \
    done; \
    echo "  No collisions found."
    @rm -rf skills agents gemini-extension.json plugin.json; \
    mkdir -p skills agents; \
    for plugin in {{plugins}}; do \
        if [ -d "plugins/$plugin/skills" ]; then \
            for entry in "plugins/$plugin/skills"/*; do \
                [ -e "$entry" ] || continue; \
                cp -R "$entry" "skills/$(basename "$entry")"; \
            done; \
        fi; \
        if [ -d "plugins/$plugin/agents" ]; then \
            for entry in "plugins/$plugin/agents"/*; do \
                [ -e "$entry" ] || continue; \
                cp -R "$entry" "agents/$(basename "$entry")"; \
            done; \
        fi; \
    done; \
    echo "  Merged skills/ and agents/ from: {{plugins}}"
    @echo "  Filtering front matter in the bundle (keeping only name, description)..."; \
    find skills agents -type f -name "*.md" -print0 | xargs -0 -r python3 scripts/filter-frontmatter.py; \
    echo "  Front matter filtered."
    @name=$(jq -r '.name' {{marketplace}}); \
    version=$(jq -r '.version' {{marketplace}}); \
    description=$(jq -r '.description' {{marketplace}}); \
    jq -n --arg name "$name" --arg version "$version" --arg description "$description" \
        '{name: $name, version: $version, description: $description}' \
        > gemini-extension.json; \
    echo "  Generated: gemini-extension.json"; \
    jq -n --arg name "$name" --arg description "$description" \
        '{"$schema": "https://antigravity.google/schemas/v1/plugin.json", name: $name, description: $description}' \
        > plugin.json; \
    echo "  Generated: plugin.json"
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


[doc("Get the running devcontainer ID (empty if not running)")]
_sandbox-id:
    @docker ps --filter "label=devcontainer.local_folder={{justfile_directory()}}" --format "{{{{.ID}}" | head -n1

[doc("""
  Start devcontainer and open an interactive shell.

  Description:
    Starts the development container using devcontainer CLI and attaches to an
    interactive zsh shell. First run may take time to build the image.

  Steps:
    1. Runs `devcontainer up` to start the container
    2. Extracts container ID, workspace folder, and user from output
    3. Attaches to the container with docker exec

  Usage:
    just sandbox
""")]
sandbox:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Starting devcontainer... First run can take long time to build the image"
    tmpfile=$(mktemp)
    devcontainer up --workspace-folder . 2>&1 | tee "$tmpfile"
    output=$(cat "$tmpfile")
    rm "$tmpfile"
    container_id=$(echo "$output" | grep -oP '"containerId"\s*:\s*"\K[^"]+')
    workspace=$(echo "$output" | grep -oP '"remoteWorkspaceFolder"\s*:\s*"\K[^"]+')
    user=$(echo "$output" | grep -oP '"remoteUser"\s*:\s*"\K[^"]+')
    if [ -z "$container_id" ]; then
        echo "Error: could not find devcontainer"
        exit 1
    fi
    echo "Attaching to container $container_id as ${user:-root} at $workspace..."
    docker exec -it -u "${user:-root}" -w "${workspace:-/}" "$container_id" zsh

[doc("""
  Attach to a running devcontainer.

  Description:
    Connects to an already running devcontainer shell. Requires that
    the devcontainer was started with `just sandbox` first.

  Steps:
    1. Gets the container ID using _sandbox-id
    2. Inspects container to find workspace and user
    3. Attaches with docker exec

  Usage:
    just attach-sandbox
""")]
attach-sandbox:
    #!/usr/bin/env bash
    set -euo pipefail
    container_id=$(just _sandbox-id)
    if [ -z "$container_id" ]; then
        echo "Error: no running devcontainer found. Run 'just sandbox' first."
        exit 1
    fi
    eval "$(docker inspect "$container_id" | python3 -c "
    import json,sys
    c = json.load(sys.stdin)[0]
    folder = c['Config']['Labels'].get('devcontainer.local_folder','')
    ws = next((m['Destination'] for m in c.get('Mounts',[]) if m['Source'] == folder), '/')
    meta = json.loads(c['Config']['Labels'].get('devcontainer.metadata','[]'))
    user = next((i['remoteUser'] for i in meta if 'remoteUser' in i), 'root')
    print(f'workspace={ws}')
    print(f'user={user}')
    ")"
    echo "Attaching to container $container_id as $user at $workspace..."
    docker exec -it -u "$user" -w "$workspace" "$container_id" zsh

[doc("""
  Stop and remove the devcontainer.

  Description:
    Gracefully stops and removes the running development container.
    Safe to run even if no container is running.

  Steps:
    1. Gets container ID (if any)
    2. Stops the container with docker stop
    3. Removes the container with docker rm

  Usage:
    just stop-sandbox
""")]
stop-sandbox:
    #!/usr/bin/env bash
    set -euo pipefail
    container_id=$(just _sandbox-id)
    if [ -z "$container_id" ]; then
        echo "No running devcontainer found."
        exit 0
    fi
    echo "Stopping container $container_id..."
    docker stop "$container_id" && docker rm "$container_id"
    echo "Done."

[doc("""
  Tear down the devcontainer docker-compose resources.

  Description:
    Runs docker compose down for the devcontainer configuration.
    Use this to completely clean up devcontainer networking and volumes.

  Usage:
    just down-devcontainer
""")]
down-devcontainer:
    docker compose --project-name decision-engine_devcontainer -f .devcontainer/docker-compose.yaml down
