#!/usr/bin/env python3
"""Total-cost accounting over a Claude Code `--output-format=stream-json` log.

WHY THIS IS ITS OWN MODULE AND NOT A METHOD ON `agent.py`'s AGENT CLASS
------------------------------------------------------------------------
The rule below is the whole substance of this harness's cost fix, so it has to
be reachable by the project's default test command
(`python3 -m unittest discover`, see README.md) -- and that interpreter has no
`pier` installed. `agent.py` cannot provide that: its top-level
`from pier.agents.installed...` imports mean merely importing it raises
ImportError without pier, so every test of a rule living inside
`ClaudeCodeSadd` would `skip` rather than run, leaving a green suite that
proves nothing about the fix. Keeping the rule here, in a module whose only
import is stdlib `json`, makes it testable with plain strings and no install;
`ClaudeCodeSadd._parse_total_cost_from_stream_json` shrinks to opening the file
and calling this.

Same pure-core/impure-shell split `collect.py` already applies with
`plugin_load_error_from_init_event` / `find_stream_log_init_event` and
`incompleteness_reason_from_signals` / `find_trial_incompleteness_reason`, and
the same reason: the judgment is unit-testable, the file reading is not.

NOT USED BY `collect.py`, DELIBERATELY
---------------------------------------
`collect.py` reports each trial's cost as pier recorded it in that trial's
`result.json`, and does not re-derive it from the stream through this function.
Re-deriving would silently restate figures for runs already on disk, so a
`results.json` would stop matching the `result.json` files it was built from.
The fix therefore corrects runs made from here on; see README.md's Cost
section, which says so out loud.
"""

from __future__ import annotations

import json
from collections.abc import Iterable


def parse_total_cost_from_stream_lines(lines: Iterable[str]) -> float | None:
    """The largest `total_cost_usd` across every `{"type":"result"}` line.

    `lines` is any iterable of raw stream lines -- an open file object (so a
    multi-gigabyte transcript never has to fit in memory), a list of strings in
    a test, anything. Returns None when no `result` line carries a usable
    number, which is "cost unknown" and deliberately not `0.0`.

    WHY NOT THE FIRST EVENT, which is what pier's own
    `ClaudeCode._parse_total_cost_from_stream_json` returns -- verified at
    `pier/agents/installed/claude_code.py:665` of `datacurve-pier==0.3.0`, the
    exact release `pyproject.toml` pins (re-check this line reference when that
    pin moves; a pier release that fixes the bug upstream makes the override
    redundant). A `claude --print`
    session with async sub-agents does not emit one terminal `result` event; it
    emits one per resumption, because every background task completion resumes
    the session (`"origin": {"kind": "task-notification"}`). Each reports the
    session's spend *cumulatively*, so the first one is the total as of the
    moment the first sub-agent finished -- a small fraction of the real bill.
    Measured on this harness's own recorded runs: 22 events spanning $0.392 to
    $26.530 (`runs/do-in-steps__sonnet-sonnet/cattrs-partial-structuring-recov__ZsbwRdJ`,
    understated 68x) and 11 spanning $0.140 to $1.804 (`runs/_preflight-do-in-steps/`,
    understated 13x). A stream with a single `result` event -- as
    `runs/_preflight/abs-stepped-slices__HyQJyYy` has -- was never affected;
    for it, first and last are the same event.

    MAX, NOT LAST, deliberately. The recorded values are cumulative and
    monotonically increasing, so both rules pick the same number on every
    stream measured here; max is the safer of two identical answers because the
    one failure mode it rules out is the one being fixed. These events are
    flushed by concurrent background tasks, so should they ever arrive out of
    order, "last" silently under-reports again while "max" cannot. Max would be
    wrong only if the values were per-turn deltas needing a sum, which the
    recorded streams rule out: the 22 deltas would sum to $282.19, an order of
    magnitude past the $28.39 that same stream's final
    `modelUsage.claude-sonnet-5.costUSD` reports.

    A `result` line whose `total_cost_usd` is null, missing or unparseable is
    SKIPPED rather than deciding the answer for the whole stream (upstream
    returns None the moment the *first* event is bad). One malformed resumption
    event must not erase a known-good total recorded by another: `None` claims
    "no cost data at all", which would be a lie while a valid figure sits
    further down. Blank lines, lines not starting with `{`, and lines that
    fail `json.loads` are skipped the same way and for the same reason --
    upstream skips them too, and a truncated final line is normal in a log
    still being written.
    """
    total_cost: float | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "result":
            continue
        try:
            cost = float(event["total_cost_usd"])
        except (KeyError, TypeError, ValueError):
            continue  # unusable event; keep looking for a valid total
        total_cost = cost if total_cost is None else max(total_cost, cost)

    return total_cost
