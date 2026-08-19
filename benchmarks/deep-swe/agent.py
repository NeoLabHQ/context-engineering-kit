"""Pier agent extension that lets Claude Code load a local plugin marketplace.

Pier (https://github.com/datacurve-ai/pier) has no notion of Claude Code
plugins -- it only knows about ``skills_dir``, which copies skill files but
not the plugin *agents* that ``sadd:do-and-judge`` and ``sadd:do-in-steps``
dispatch to. `ClaudeCodeSadd` closes that gap with the smallest possible
subclass: it teaches pier the `--plugin-dir` flag, checks out a pinned copy
of this repo into the container so that path exists, and allowlists the
domain the checkout needs. Everything else -- prompt rendering, trajectory
parsing, container lifecycle -- stays exactly as `ClaudeCode` implements it.

Used via: `pier run --agent-import-path agent:ClaudeCodeSadd ...` with pier's
working directory set to this file's directory (see run.py).
"""

from pier.agents.installed.base import CliFlag
from pier.agents.installed.claude_code import ClaudeCode
from pier.models.agent.install import AgentInstallSpec, InstallStep
from pier.models.agent.network import NetworkAllowlist

# The cost-parsing rule this class overrides pier's version with. Kept in a
# pier-free module so it is testable without pier -- see its docstring.
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
