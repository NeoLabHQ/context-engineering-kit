#!/bin/bash
input=$(cat)

# === ORIGINAL FIRST LINE (with 2 text substitutions) ===
model=$(echo "$input" | jq -r '.model.display_name // .model.id')
style=$(echo "$input" | jq -r '.output_style.name // "default"')
total_input=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
total_output=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
context_size=$(echo "$input" | jq -r '.context_window.context_window_size // 0')
total_used=$((total_input + total_output))
if [ "$context_size" -gt 0 ]; then
  percentage=$(awk "BEGIN {printf \"%.1f\", ($total_used / $context_size) * 100}")
else
  percentage="0.0"
fi
if [ "$total_used" -ge 1000 ]; then
  used_display=$(awk "BEGIN {printf \"%.1fK\", $total_used / 1000}")
else
  used_display="${total_used}"
fi
if [ "$context_size" -ge 1000 ]; then
  size_display=$(awk "BEGIN {printf \"%.0fK\", $context_size / 1000}")
else
  size_display="${context_size}"
fi
git_branch=$(git -c core.fileMode=false config advice.detachedHead false 2>/dev/null && git branch --show-current 2>/dev/null || echo "no-git")

# Session duration
duration_ms=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')
duration_sec=$((duration_ms / 1000))
dur_mins=$((duration_sec / 60))
dur_secs=$((duration_sec % 60))
session_dur="${dur_mins}m ${dur_secs}s"

printf '\033[01;36m%s\033[00m \033[90m|\033[00m \033[01;33mStyle: %s\033[00m \033[90m|\033[00m \033[01;35m%s/%s (%s%%)\033[00m \033[90m|\033[00m \033[01;32m%s\033[00m \033[90m|\033[00m \033[2;37mEsc: interrupt\033[00m \033[90m|\033[00m \033[2;37mShift + Enter: new line\033[00m \033[90m|\033[00m \033[2;37m⏱️ %s\033[00m\n' "$model" "$style" "$used_display" "$size_display" "$percentage" "$git_branch" "$session_dur"

# === Change 3: Add current/weekly usage lines ===

dot_bar() {
  local p=$1 t=10 b="" i
  local f=$(((p*t+50)/100))
  for i in $(seq 1 $t); do
    if [ $i -le $f ]; then b="${b}● "; else b="${b}○ "; fi
  done
  printf "%s" "${b% }"
}

fmt_dur() {
  local s=$1
  if [ $s -lt 60 ]; then echo "${s}s"
  elif [ $s -lt 3600 ]; then echo "$((s/60))min"
  else local h=$((s/3600)) m=$(((s%3600)/60)); [ $m -eq 0 ] && echo "${h}hr" || echo "${h}hr ${m}min"
  fi
}

# Session line - uses ccusage blocks --active for real data
block_json=$(npx -y ccusage blocks --json --active 2>/dev/null)
block_cost=$(echo "$block_json" | jq -r '.blocks[0].costUSD // 0')
block_remaining=$(echo "$block_json" | jq -r '.blocks[0].projection.remainingMinutes // 0')
block_total_cost=$(echo "$block_json" | jq -r '.blocks[0].projection.totalCost // 0')

# Calculate block usage percentage (projected cost out of a 5hr block)
# Use actual cost vs projected total as progress indicator
if [ "$block_total_cost" != "0" ] && [ "$block_total_cost" != "null" ]; then
  block_pct=$(awk "BEGIN {v=($block_cost / $block_total_cost) * 100; printf \"%.0f\", v}")
else
  block_pct=0
fi
[ "$block_pct" -gt 100 ] 2>/dev/null && block_pct=100

cur_bar=$(dot_bar "$block_pct")

# Format remaining time
remaining_int=$(printf "%.0f" "$block_remaining")
if [ "$remaining_int" -ge 60 ]; then
  rem_h=$((remaining_int / 60))
  rem_m=$((remaining_int % 60))
  [ $rem_m -eq 0 ] && rem_display="${rem_h}hr" || rem_display="${rem_h}hr ${rem_m}min"
else
  rem_display="${remaining_int}min"
fi

# Format cost
block_cost_fmt=$(printf '$%.2f' "$block_cost")

printf 'session %s  %d%%  ↻ %s till refresh\n' "$cur_bar" "$block_pct" "$rem_display"
