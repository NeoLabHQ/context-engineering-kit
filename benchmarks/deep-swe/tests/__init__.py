"""Test package for `collect.py`/`report.py`'s pure functions.

Patches `sys.path` exactly once, when this package is first imported (which
always happens before any of its test modules load, per Python's import
semantics), so every test module below can simply `import collect` / `import
report` without repeating the patch itself. `collect.py`/`report.py` live one
directory up (`benchmarks/deep-swe/`), not inside this `tests/` package --
mirrors run.py's own sys.path patch ahead of `import agent`.

Run the whole suite with `python3 -m unittest discover` from
`benchmarks/deep-swe/` (see that directory's README.md). Stdlib `unittest`
only -- no third-party install step, no `pier`.
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent.parent
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))
