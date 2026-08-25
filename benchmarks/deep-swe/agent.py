"""Pier agent extension that lets Claude Code load a local plugin marketplace.

Pier (https://github.com/datacurve-ai/pier) has no notion of Claude Code
plugins -- it only knows about ``skills_dir``, which copies skill files but
not the plugin *agents* that ``sadd:do-and-judge`` and ``sadd:do-in-steps``
dispatch to. `ClaudeCodeSadd` closes that gap with the smallest possible
subclass: it teaches pier the `--plugin-dir` flag, checks out a pinned copy
of this repo into the container so that path exists, and allowlists the
domain the checkout needs. Two further overrides correct upstream behaviour
this benchmark cannot live with -- `exec_as_agent` (pier pins every model
alias to the orchestrator's model behind a gateway base URL, erasing the
implementation-tier axis) and `_parse_total_cost_from_stream_json` (pier reads
only the first `result` event, understating any resumed session). Everything
else -- prompt rendering, trajectory building, container lifecycle -- stays
exactly as `ClaudeCode` implements it.

Used via: `pier run --agent-import-path agent:ClaudeCodeSadd ...` with pier's
working directory set to this file's directory (see run.py).
"""

from typing import Any

from pier.agents.installed.base import CliFlag
from pier.agents.installed.claude_code import ClaudeCode
from pier.environments.base import BaseEnvironment
from pier.models.agent.install import AgentInstallSpec, InstallStep
from pier.models.agent.network import NetworkAllowlist

# The two rules this class overrides pier's behaviour with. Both kept in
# pier-free modules so they are testable without pier -- see their docstrings.
from model_alias_pins import without_gateway_alias_pins
from stream_cost import parse_total_cost_from_stream_lines

# Pinned to the `plugins/sadd` release this benchmark harness was built
# against, not "main" -- every run must clone an identical tree. CEK_REF may
# be a tag, a branch, or a raw commit SHA (the checkout below resolves all
# three uniformly); bump by updating CEK_REF to a newer value. Downstream
# scripts (collect.py, report.py) import this constant to record which
# plugin version produced a run.
CEK_REPO = "https://github.com/NeoLabHQ/context-engineering-kit.git"
CEK_REF = "v3.8.1"
CEK_INSTALL_DIR = "/tmp/context-engineering-kit"


class ClaudeCodeSadd(ClaudeCode):
    """`ClaudeCode`, extended with plugin-dir support and a plugin checkout."""

    # Lets run.py pass `--ak plugin_dir=<path>`; pier renders this into
    # `--plugin-dir <path>` on the `claude --print` command line.
    CLI_FLAGS = ClaudeCode.CLI_FLAGS + [
        CliFlag("plugin_dir", cli="--plugin-dir", type="str"),
    ]

    def install_spec(self) -> AgentInstallSpec:
        """Extend the base Claude Code install with a pinned CEK checkout."""
        spec = super().install_spec()

        # ClaudeCode's own install only ensures curl/bash/node are present;
        # git is additive and specific to this subclass's needs.
        install_git = (
            "if command -v apk &> /dev/null; then apk add --no-cache git; "
            "elif command -v apt-get &> /dev/null; then apt-get update && apt-get install -y git; "
            "elif command -v yum &> /dev/null; then yum install -y git; fi"
        )
        # `rm -rf` first so re-running setup() after a partial failure doesn't
        # hit git's "destination path already exists" error. `git clone
        # --branch` only resolves branches/tags, not raw commit SHAs, so
        # instead init + fetch the pinned ref directly + checkout FETCH_HEAD:
        # that form works uniformly whether CEK_REF is a branch, a tag, or a
        # commit SHA. The `&&` chain means any failure (bad ref, network
        # error) aborts the step and fails the container build loudly.
        clone_cek = (
            f"rm -rf {CEK_INSTALL_DIR} && "
            f"git init -q {CEK_INSTALL_DIR} && "
            f"git -C {CEK_INSTALL_DIR} remote add origin {CEK_REPO} && "
            f"git -C {CEK_INSTALL_DIR} fetch --depth 1 origin {CEK_REF} -q && "
            f"git -C {CEK_INSTALL_DIR} checkout -q FETCH_HEAD"
        )
        # Two steps, not one: `InstallStep.user` maps 1:1 to a Dockerfile
        # `USER` directive, so a single step can't run part of its command as
        # root (needed to apt/apk/yum install git) and part as `agent`
        # (needed so the checkout is owned by the user that later runs
        # Claude Code with --plugin-dir). Pier's install-step model makes
        # that split structural, not a style choice.
        spec.steps.append(InstallStep(user="root", run=install_git))
        spec.steps.append(InstallStep(user="agent", run=clone_cek))
        return spec

    def network_allowlist(self) -> NetworkAllowlist:
        """Allow the CEK clone alongside whatever ClaudeCode already needs."""
        allowlist = super().network_allowlist()
        return NetworkAllowlist(domains=[*allowlist.domains, "github.com"])

    async def exec_as_agent(
        self,
        environment: BaseEnvironment,
        command: str,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
        timeout_sec: int | None = None,
    ) -> Any:
        """Run pier's command, minus its gateway model-alias pins.

        Overrides `BaseInstalledAgent.exec_as_agent` (pier's
        `agents/installed/base.py:377`) purely to filter `env` on the way
        through; the command, the container and every other parameter are
        forwarded untouched. What it counteracts, and why removing it silently
        collapses `opus-sonnet` into `opus-opus`, is documented in
        `model_alias_pins.without_gateway_alias_pins` -- a pier-free module so
        the rule is testable under the default test command.

        WHY THIS HOOK AND NOT `--ae`
        -----------------------------
        `run.py`'s `AGENT_ENV` can only ever SET a variable, and what is
        needed here is for these four to be ABSENT, so that Claude Code falls
        back to its own alias resolution. `--ae ANTHROPIC_DEFAULT_HAIKU_MODEL=`
        would put an empty string in the container's environment instead --
        not the same thing, and not something upstream documents a meaning
        for. (Setting them to a value is not an option either at the point
        `run.py` runs: `build_process_env` merges `--ae` at
        `claude_code.py:1265`, above the pinning block at `:1290-1295`, and
        `_exec` merges it again at `base.py:320-323`, below -- so an operator
        who deliberately passes one of these four via `--ae` still wins, and
        this filter will not fight them.)

        That second merge is why this hook is not the only way to overrule
        `run()`; it is only the way to overrule it by REMOVAL. Anything that
        just needs a different VALUE than the one `run()` wrote -- including
        `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, which `run()` hardcodes at
        `claude_code.py:1302` -- goes through `run.py`'s `FORWARDED_HOST_ENV`
        instead, and that constant's comment says why. Do not add such a
        variable here.

        `exec_as_agent` is the last hook a SUBCLASS controls on the way to the
        container -- `_extra_env` still merges after it, which is the whole
        point of the paragraph above; `claude_code.py:1336` and `:1341` are
        its two callers, one per command `run()` issues.

        `install()` routes its `user="agent"` steps through here too
        (`base.py:406`), with each step's own small `env` (`None` for every
        step this class or `ClaudeCode` declares). The filter is a no-op on
        those: it acts only when `ANTHROPIC_BASE_URL` and `ANTHROPIC_MODEL`
        are both present, which no install step's env has.
        """
        return await super().exec_as_agent(
            environment,
            command,
            env=without_gateway_alias_pins(env),
            cwd=cwd,
            timeout_sec=timeout_sec,
        )

    def _parse_total_cost_from_stream_json(self) -> float | None:
        """The stream's *total* cost, not the first `result` event's running total.

        Overrides `ClaudeCode`'s version (pier's `claude_code.py`, same method
        name), which returns at the FIRST `{"type":"result"}` line it finds and
        so reports a fraction of the real bill for any session that resumed.
        The rule that replaces it -- and the evidence for reading these events
        as cumulative, why max rather than last, and what a null/missing cost
        field does -- lives in `stream_cost.parse_total_cost_from_stream_lines`,
        a module with no `pier` import so it stays testable under the project's
        default test command. This method is only the I/O around it.

        Upstream's edge cases are preserved exactly: a missing or unreadable
        log returns None, and so does a stream with no usable `result` event.
        Two deliberate differences, both in this shell rather than the rule:
        the file is iterated line by line instead of read whole, so a 6 MB (or
        600 MB) transcript never has to fit in memory; and `errors="replace"`
        is passed for the reason collect.py documents on `load_json_or_none`,
        namely that a log truncated mid-multibyte-character by an interrupted
        job would otherwise raise `UnicodeDecodeError` -- which upstream's
        `except OSError` does not catch -- out of trajectory building. A
        replacement character can only corrupt the one line it lands on, which
        then fails `json.loads` and is skipped like any other malformed line.
        """
        stream_path = self.logs_dir / "claude-code.txt"
        try:
            with stream_path.open(encoding="utf-8", errors="replace") as stream_lines:
                return parse_total_cost_from_stream_lines(stream_lines)
        except OSError:
            return None
