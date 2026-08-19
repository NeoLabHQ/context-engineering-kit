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
