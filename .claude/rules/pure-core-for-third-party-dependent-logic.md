---
title: Put Judgment Logic in a Pure Helper, Not Behind a Third-Party Import
impact: HIGH
paths:
  - "**/*.py"
---

# Put Judgment Logic in a Pure Helper, Not Behind a Third-Party Import

When new decision logic lands in a module whose top-level imports are not installed for the
project's default test command, every test covering that logic silently *skips* rather than runs —
a green suite that proves nothing. Extract the judgment into a module-level pure function the
subclass/method delegates to, so the rule is reachable with plain values and no install.

## Incorrect

The whole parsing rule lives inside a method of a class that inherits from a third-party base, so
`python3 -m unittest discover` reports `OK (skipped=11)` and the fix is asserted, never executed.

```python
from third_party.base import Base          # not installed for the default test runner

class Extended(Base):
    def _parse_total(self) -> float | None:
        best = None
        for line in (self.logs_dir / "log.txt").read_text().splitlines():
            ...                              # the actual rule, unreachable without third_party
        return best
```

## Correct

The rule becomes a pure function; the override shrinks to I/O plus a call. Tests import the helper
directly and run everywhere; one thin test still pins the override's resolution order.

```python
def parse_total_from_lines(lines: Iterable[str]) -> float | None:
    """The rule, pure and testable with plain strings."""
    best = None
    for line in lines:
        ...
    return best

class Extended(Base):
    def _parse_total(self) -> float | None:
        return parse_total_from_lines(read_lines_or_empty(self.logs_dir / "log.txt"))
```

## Reference

- Established in-repo precedent: `collect.py`'s `plugin_load_error_from_init_event` and
  `incompleteness_reason_from_signals`, each split from its file-reading counterpart for exactly
  this reason.
