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


# Get the running devcontainer ID (empty if not running)
_sandbox-id:
    @docker ps --filter "label=devcontainer.local_folder={{justfile_directory()}}" --format "{{{{.ID}}" | head -n1

# Start devcontainer and open an interactive shell
sandbox:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Starting devcontainer... First run can take long time to build the image"
    output=$(devcontainer up --workspace-folder .) # TODO: print output during the process
    echo "$output"
    container_id=$(echo "$output" | grep -oP '"containerId"\s*:\s*"\K[^"]+')
    workspace=$(echo "$output" | grep -oP '"remoteWorkspaceFolder"\s*:\s*"\K[^"]+')
    user=$(echo "$output" | grep -oP '"remoteUser"\s*:\s*"\K[^"]+')
    if [ -z "$container_id" ]; then
        echo "Error: could not find devcontainer"
        exit 1
    fi
    echo "Attaching to container $container_id as ${user:-root} at $workspace..."
    docker exec -it -u "${user:-root}" -w "${workspace:-/}" "$container_id" zsh

# Attach to a running devcontainer
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

# Stop and remove the devcontainer
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


# Run claude with a prompt and stream plain text output
[no-exit-message]
claude prompt:
    #!/usr/bin/env bash
    set -euo pipefail
    # Usage:
    #   just claude "Explain this codebase"
    #   just claude "Summarize the README"
    #
    # Streams claude's response as plain text to stdout.
    # Uses stream-json format with jq to extract text deltas.
    claude -p "{{ prompt }}" --output-format stream-json --verbose --include-partial-messages | \
      jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'

# Create a new draft task from a prompt
[no-exit-message]
claude-add-task prompt:
    #!/usr/bin/env bash
    set -euo pipefail
    # Usage:
    #   just claude-add-task "Add validation to the /decide endpoint"
    just claude "/sdd:add-task {{ prompt }}"

# Plan a draft task and then implement it
[no-exit-message]
claude-plan-and-implement task-filename:
    #!/usr/bin/env bash
    set -euo pipefail
    # Usage:
    #   just claude-plan-and-implement my-task.test.md
    #
    # 1. Verifies the task file exists in .specs/tasks/draft/
    # 2. Runs /sdd:plan to move it to .specs/tasks/todo/
    # 3. Verifies the file arrived in todo/
    # 4. Runs /sdd:implement on the planned task
    draft=".specs/tasks/draft/{{ task-filename }}"
    todo=".specs/tasks/todo/{{ task-filename }}"
    if [ ! -f "$draft" ]; then
      echo "Error: task file not found: $draft"
      exit 1
    fi
    echo "==> Planning: $draft"
    just claude "/sdd:plan @$draft"
    if [ ! -f "$todo" ]; then
      echo "Error: planning did not produce: $todo"
      exit 1
    fi
    echo ""
    echo "==> Implementing: $todo"
    just claude "/sdd:implement @$todo"

down-devcontainer:
    docker compose --project-name decision-engine_devcontainer -f .devcontainer/docker-compose.yaml down