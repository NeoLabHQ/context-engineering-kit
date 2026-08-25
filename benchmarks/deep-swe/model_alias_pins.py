"""The rule for undoing pier's gateway model-alias pinning.

WHAT PIER DOES
---------------
When a run has both a custom base URL and a model name, pier's
`ClaudeCode.run()` rewrites every model alias to the orchestrator's own model
(`pier/agents/installed/claude_code.py:1290-1295` in datacurve-pier 0.3.1,
under the comment "When using custom base URL, set all model aliases to the
same model")::

    if "ANTHROPIC_BASE_URL" in env and "ANTHROPIC_MODEL" in env:
        env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = env["ANTHROPIC_MODEL"]
        env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = env["ANTHROPIC_MODEL"]
        env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = env["ANTHROPIC_MODEL"]
        env["CLAUDE_CODE_SUBAGENT_MODEL"] = env["ANTHROPIC_MODEL"]

That is a reasonable default for a gateway serving exactly one model, and it
is fatal to this benchmark. Every plugin arm's prompt is
`/{skill} --model {impl} ...`, and the sadd skills dispatch their
implementation and judge sub-agents at that bare tier name -- so the arm's
implementation tier reaches Claude Code as the alias `haiku`, `sonnet` or
`opus`. Pinned, the mixed arms (`opus-sonnet`, `sonnet-haiku`) run their
sub-agents at the ORCHESTRATOR's model, collapsing into `opus-opus` and
`sonnet-sonnet`. `CLAUDE_CODE_SUBAGENT_MODEL` pins the same thing a second
way, from the other end. Nothing in `results.json` would show it: the arm id
is derived from what was requested, not from what ran, so a gateway-routed
sweep would report a tier axis it never actually measured.

WHY THIS IS A REMOVAL, NOT A REMAPPING
---------------------------------------
Removing the four leaves Claude Code to resolve `haiku`/`sonnet`/`opus`
itself, which is what an unpinned first-party run does. This assumes the
gateway resolves those bare aliases -- see README.md's "Gateway / proxy
routing" bullet, which states that assumption as the operator's to check.
Remapping them onto concrete model ids instead would put a second copy of the
tier-to-model table here, next to `run.py`'s `MODEL_IDS`, free to drift.

WHY THIS MODULE HAS NO `pier` IMPORT
-------------------------------------
Same reason `stream_cost.py` does not: `agent.py` imports `pier`, which is
installed only in the pier venv, so a rule living there would be covered by
tests that skip rather than run under the project's default
`python3 -m unittest discover`. The rule is here and covered unconditionally
by `tests/test_model_alias_pins.py`; `ClaudeCodeSadd.exec_as_agent` is reduced
to calling it on the env dict pier hands over.
"""

from __future__ import annotations

# The four variables pier's block above adds -- no more, no less. Anything
# else in that env dict is pier's to decide and is passed through untouched.
GATEWAY_PINNED_ALIAS_VARS = (
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL",
)

# The exact condition guarding pier's block (`claude_code.py:1291`). Keyed off
# the same two names so that a run pier never pinned is a run this rule never
# touches -- see `without_gateway_alias_pins`.
PINNING_TRIGGER_VARS = ("ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL")


def without_gateway_alias_pins(env: dict[str, str] | None) -> dict[str, str] | None:
    """`env` minus the four alias pins, but only if pier would have added them.

    Mirrors pier's own guard rather than testing for the four names directly:
    a first-party run (no `ANTHROPIC_BASE_URL`) is returned as the very same
    object, so "no gateway" provably means "no change", not "a change that
    happened to remove nothing". `env` is never mutated -- pier reuses one
    dict across both of its `exec_as_agent` calls.
    """
    if env is None:
        return None
    if not all(name in env for name in PINNING_TRIGGER_VARS):
        return env

    return {
        key: value for key, value in env.items() if key not in GATEWAY_PINNED_ALIAS_VARS
    }
