"""Shared, importable handle on `run.py` for every `test_run_*.py` file.

WHY THIS MODULE EXISTS
-----------------------
`run.py` does `import agent`, and `agent.py` imports `pier` -- a package
installed only in the dedicated pier venv, not in the plain interpreter this
suite normally runs under. Every test file that needs `run` therefore has to
register a stub `agent` module carrying the two constants `run.py` reads before
importing it. Doing that inline in each file meant three copies of the same
eight lines, able to drift apart on which constants the stub carries; this
module is the single copy, and `from .run_fixtures import run` is how a test
file gets `run` with the stub already in place.

THE STUB IS A FALLBACK, NOT A DEFAULT
--------------------------------------
It is installed only when the real `agent` cannot work -- i.e. when `pier` is
not importable -- and never when it already is. Registering it unconditionally
would poison `sys.modules["agent"]` for the whole session, and
`test_agent_cost_parsing.py` needs the REAL `agent` (its subject is an override
of a method inherited from pier's `ClaudeCode`, which a stub cannot stand in
for). Because pytest imports every test module during collection, before any
test runs, whichever module got there first would otherwise decide what
`agent` means for all of them.

Nothing else in `run.py` -- command building, the pier subprocess, the
container lifecycle -- becomes exercisable this way; see README.md's "Running
the tests" section for what covers those instead.
"""

from __future__ import annotations

import importlib.util
import sys
import types

_PIER_AVAILABLE = importlib.util.find_spec("pier") is not None

if "agent" not in sys.modules and not _PIER_AVAILABLE:
    _agent_stub = types.ModuleType("agent")
    _agent_stub.CEK_REF = "v0.0.0-test-stub"
    _agent_stub.CEK_INSTALL_DIR = "/tmp/context-engineering-kit"
    sys.modules["agent"] = _agent_stub

import run  # noqa: E402 -- must follow the `agent` stub above

__all__ = ["run"]
