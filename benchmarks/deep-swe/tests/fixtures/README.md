# Test fixtures

## `recorded-result-events.txt`

Every `{"type":"result"}` line from the recorded stream

    runs/do-in-steps__sonnet-sonnet/cattrs-partial-structuring-recov__ZsbwRdJ/agent/claude-code.txt

trimmed to the keys the cost parser reads (`type`, `total_cost_usd`) plus
`subtype`/`origin` for context. The costs are verbatim; nothing was rounded,
reordered or invented. The full originals carry multi-KB `usage`/`modelUsage`
blocks, and the whole transcript is 6 MB, which is why this is a trimmed copy
rather than the file itself.

It exists so `tests/test_stream_cost.py` can assert the real cost sequence
**unconditionally** — `runs/` is a recorded artifact that may not be present in
every checkout, and a test that skips when it is missing proves nothing. The
same test additionally re-reads the original in place when it *is* present, and
fails if the two ever disagree, so this copy cannot silently drift from its
source.

Regenerate (from `benchmarks/deep-swe/`) with:

```bash
python3 - <<'EOF'
import json
from pathlib import Path

source = Path("runs/do-in-steps__sonnet-sonnet/cattrs-partial-structuring-recov__ZsbwRdJ/agent/claude-code.txt")
header = Path("tests/fixtures/recorded-result-events.txt").read_text().splitlines()
header = [line for line in header if line.startswith("#")]
events = []
for raw in source.read_text(encoding="utf-8", errors="replace").splitlines():
    raw = raw.strip()
    if not raw.startswith("{"):
        continue
    event = json.loads(raw)
    if event.get("type") != "result":
        continue
    trimmed = {"type": event["type"], "subtype": event.get("subtype")}
    if "origin" in event:
        trimmed["origin"] = event["origin"]
    trimmed["total_cost_usd"] = event.get("total_cost_usd")
    events.append(json.dumps(trimmed))
Path("tests/fixtures/recorded-result-events.txt").write_text("\n".join(header + events) + "\n")
EOF
```

## `recorded-rate-limit-events.txt`

The five distinct `rate_limit_event` / `result` shapes that
`triage.api_fault_from_stream_lines` has to tell apart, all taken verbatim from
recorded transcripts, laid out in the order a real quota exhaustion produces
them:

| Line | Source | What it is |
|---|---|---|
| 3 | `do-in-steps__sonnet-sonnet__abs-stepped-slices/…__tqkGk6o`, line 12 | `status: "allowed"` — a served request. Note `overageStatus: "rejected"` on it, which is why that field is deliberately not a marker. |
| 4 | `do-in-steps__opus-opus__abs-stepped-slices/…__fAGX8MS`, line 6 | `status: "allowed_warning"` — the seven-day utilization notice. Also a served request; reading it as a denial is the defect this fixture exists to pin. |
| 5 | same transcript, line 2537 | a second `allowed_warning`, five-hour window at 0.9 utilization. |
| 6 | same transcript, line 2936 | `status: "rejected"` — the one real denial in this repository. |
| 7 | same transcript, line 2941 | the `result` event five lines later, `api_error_status: 429`, `is_error: true`. |

Only line 7 is trimmed, to the keys the triage reads plus `subtype`/
`is_error`/`terminal_reason`/`stop_reason`/`num_turns`/`total_cost_usd` for
context: the original carries multi-KB `usage`/`modelUsage` blocks. Every
`rate_limit_event` line is byte-for-byte its original.

It exists for the same reason as the cost fixture above — so
`tests/test_triage.py` can assert the real status vocabulary and the real
worst-fault-wins ordering **unconditionally**, in a checkout where `runs/` (a
gitignored recorded artifact) is absent. The same test file additionally
re-triages the original job directories when they *are* present, so this copy
cannot silently drift from the runs it was read from.
