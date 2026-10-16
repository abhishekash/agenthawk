# SpanHound

<!-- mcp-name: io.github.abhishekash/spanhound -->

[![CI](https://github.com/abhishekash/spanhound/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/abhishekash/spanhound/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/spanhound)](https://pypi.org/project/spanhound/)
[![Downloads](https://img.shields.io/pypi/dm/spanhound?label=downloads%2Fmonth)](https://pypistats.org/packages/spanhound)
[![GitHub release](https://img.shields.io/github/v/release/abhishekash/spanhound)](https://github.com/abhishekash/spanhound/releases/latest)
[![GitHub stars](https://img.shields.io/github/stars/abhishekash/spanhound?style=social)](https://github.com/abhishekash/spanhound/stargazers)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-listed-2e8b57)](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.abhishekash%2Fspanhound/versions)
[![Glama MCP server](https://glama.ai/mcp/servers/abhishekash/spanhound/badges/score.svg)](https://glama.ai/mcp/servers/abhishekash/spanhound)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/abhishekash/spanhound/blob/main/LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)

**Capture local agent traces. Ask your MCP client what happened.** SpanHound
(formerly mcp-trace-inspector) captures supported Python agent calls, receives
OpenTelemetry over local OTLP/HTTP, and exposes read-only MCP tools for
failures, approval decisions, token usage, and run comparisons. It reads JSONL
spans and OTLP JSON exports as described in the
[user guide](https://github.com/abhishekash/spanhound/blob/main/docs/user-guide.md), including traces from
[agent-harness](https://github.com/abhishekash/agent-harness).

<p align="center">
  <a href="https://github.com/abhishekash/spanhound/blob/main/docs/media/shell-root-escape-demo.mp4">
    <img src="https://raw.githubusercontent.com/abhishekash/spanhound/main/docs/media/shell-root-escape-preview.gif" width="960" alt="Animated demo: a blocked tool call becomes an inspectable trace" />
  </a>
</p>

**Demo:** [Watch the full 48-second video](https://github.com/abhishekash/spanhound/blob/main/docs/media/shell-root-escape-demo.mp4) · [Read the reproducible story](https://github.com/abhishekash/spanhound/blob/main/docs/shell-boundary-story.md). This is a scripted regression trace, not a live-model benchmark.

The project's concrete origin was a shell-boundary regression: the harness blocked
`cat ../outside.txt`, but the old trace recorded only that `run_shell` was
called, not the returned diagnostic. SpanHound and the harness now preserve and
query that bounded error.

## Try it in one command

```bash
uvx spanhound demo
```

```text
SpanHound demo — recorded agent failure
Tool: run_shell
Failure: error: shell path escapes workspace root: '../outside.txt'
Approval: approve (auto)
Trace: 563e779ee8fa2d7069fc63ed2cf9c8ec (6 spans)
```

The demo shows a recorded `run_shell` failure and its approval evidence from a
bundled scripted regression trace. It needs no clone, account, trace backend, or
MCP client. To inspect your own traces, point SpanHound at a directory of JSONL
spans or saved OTLP JSON exports:

```bash
uvx spanhound --trace-dir /path/to/traces --check
```

`--check` prints the runs it found and exits. Connect an MCP client with the
[configuration below](https://github.com/abhishekash/spanhound#client-configuration) to ask questions about those runs.

## Explore the repository fixtures

```bash
git clone https://github.com/abhishekash/spanhound.git
cd spanhound
uvx --from . spanhound --trace-dir examples --check
```

`--check` also reports a missing directory or malformed complete JSONL or OTLP
JSON record.

To try an OTLP JSON export, run the same command with `--trace-dir tests/fixtures`.
The [sample export](https://github.com/abhishekash/spanhound/blob/main/tests/fixtures/otlp_trace.json) includes a model call, token
usage, a tool call, and an exception.

## Capture your own traces

For a Python agent, install SpanHound's optional auto instrumentation **in the
same environment as the agent**, then run it through SpanHound:

```bash
python -m pip install 'spanhound[auto]'
spanhound run --trace-dir ./traces -- python agent.py
```

The command starts and stops a local receiver, configures OTLP export, and
captures supported library calls without changes to `agent.py`. The optional
package includes instrumentation for OpenAI, Anthropic, OpenAI Agents, HTTPX,
and Requests. It reports when no spans were produced. Your Python agent and
SpanHound must share one environment; for a uv project, use
`uv add 'spanhound[auto]'` and `uv run spanhound run -- python agent.py`.
See the [Python capture guide](https://github.com/abhishekash/spanhound/blob/main/docs/user-guide.md#capture-a-python-agent-in-one-command).

For other runtimes, or agents that already export OpenTelemetry traces, start
the receiver in one terminal:

```bash
uvx spanhound collect --trace-dir ./traces
```

Point an agent that **already uses an OpenTelemetry trace exporter** at the
receiver, then run the agent:

```bash
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces
export OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf
# Start your instrumented agent here.
```

SpanHound stores each accepted OTLP/HTTP trace request as a local JSON file.
Run `uvx spanhound --trace-dir ./traces --check` to see the captured runs, then
connect your MCP client to that folder. The receiver accepts OTLP/HTTP JSON or
protobuf on loopback; it does not add instrumentation to an agent. See the
[capture guide](https://github.com/abhishekash/spanhound/blob/main/docs/user-guide.md#capture-otlp-traces) for limits and privacy.

## Where it fits

For a live terminal and browser view of local Codex/Claude Code sessions and
received OTLP telemetry, try [Agent Observatory](https://github.com/abhishekash/agent-observatory).
SpanHound provides trace investigation through MCP using JSONL and OTLP JSON files.

Use this when you want a local trace view through MCP without setting up a
trace backend. Capture supported Python library calls in one command, receive
OTLP/HTTP from another runtime, or read the [supported JSONL or OTLP JSON
formats](https://github.com/abhishekash/spanhound/blob/main/docs/user-guide.md#requirements). Focused queries include recorded
approval decisions, bounded failure diagnostics, and run comparisons.

[MCP Agent Trace Inspector](https://github.com/dbsectrainer/mcp-agent-trace-inspector)
records steps into a local SQLite database and provides a dashboard and
exports. SpanHound auto-instruments supported Python libraries or receives
OTLP/HTTP traces, then queries the captured files through MCP. It does not
automatically trace arbitrary agent functions or approvals.

For traces stored in Jaeger, Tempo, or Traceloop, use a backend-connected tool
such as [OpenTelemetry MCP Server](https://github.com/traceloop/opentelemetry-mcp-server).
For a trace UI, instrumentation, and evaluations, see
[Phoenix](https://github.com/Arize-ai/phoenix). SpanHound does not read
backend-specific JSON exports.

## AI-native use cases

| Question during an agent run | MCP tool | Evidence returned |
|---|---|---|
| "Why did yesterday's run stall?" | `list_runs` → `slowest_spans` | Run IDs and the longest model or tool spans. |
| "Did the agent act after I denied the write?" | `approval_log` → `span_tree` | The recorded decision and subsequent execution path. |
| "How many model tokens did this run use?" | `token_usage` → `span_tree` | Run-level usage totals and the span tree for context. |
| "Which tool is failing or timing out?" | `failure_report` / `tool_stats` | Redacted diagnostics, error rates, denials, and p95 latency. |
| "Who/what was allowed to act?" | `security_audit` | Caller, tenant, server provenance, risk, and missing-evidence findings. |
| "What is happening in the run right now?" | `recent_activity` | Cursor-based polling of newly written spans. |
| "Did this model/version regress?" | `compare_runs` | Cost, latency, tokens, tool calls, and failure deltas. |

The tools read stored traces and can poll files being written, but they do not push events or infer intent from the final answer. Start with the [installation and user guide](https://github.com/abhishekash/spanhound/blob/main/docs/user-guide.md), then see the [real trace fixture](https://github.com/abhishekash/spanhound/blob/main/examples/example_trace.jsonl) and the [tool descriptions](https://github.com/abhishekash/spanhound/blob/main/src/mcp_trace/server.py) for the query contract.

## Install & run

```bash
uvx spanhound --trace-dir ./traces
# or, for local development:
git clone https://github.com/abhishekash/spanhound
cd spanhound
uvx --from . spanhound --trace-dir ./traces
```

For a desktop client that accepts [MCP Bundles](https://github.com/modelcontextprotocol/mcpb),
download the `.mcpb` asset from the [latest release](https://github.com/abhishekash/spanhound/releases/latest)
and install the downloaded file in the client; the download link does not open
a web page. In Claude Desktop, use **Settings → Extensions → Advanced settings →
Install Extension…** and select the `.mcpb` file. The bundle asks you to choose
a local trace folder.
It uses UV to install its Python dependencies on first run. SpanHound reads
the folder locally; the connected client receives the evidence returned by its
MCP tools.

If you previously ran `uvx mcp-trace-inspector`, change that command to
`uvx spanhound` to receive this release. The old PyPI distribution stays at
`0.3.1`; the new package retains its Python import paths and command aliases
for clients that install `spanhound` explicitly.

## Client configuration

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "agent-traces": {
      "command": "uvx",
      "args": ["spanhound", "--trace-dir", "/path/to/traces"]
    }
  }
}
```

**pi** (`~/.pi/agent/settings.json`):

```json
{
  "mcpServers": {
    "agent-traces": {
      "command": "uvx",
      "args": ["spanhound", "--trace-dir", "/path/to/traces"]
    }
  }
}
```

**agent-harness** (mounted as gated tools):

```bash
harness run "Why was my last run slow?" --mcp "uvx spanhound --trace-dir ./traces"
```

## Tools

| Tool | Use it when |
|---|---|
| `list_runs` | Starting out — recent runs with task, model, duration, cost, decision counts |
| `run_summary` | One run at a glance (accepts trace-id prefix) |
| `span_tree` | "What did the agent actually do?" — nested shape of the run |
| `slowest_spans` | "Why was it slow?" — top-k spans by duration |
| `approval_log` | HITL audit — every approve/deny/**edit**, who decided, and *the rationale* |
| `token_usage` | Cost questions — aggregated across runs or per-run |
| `search_spans` | Find spans by tool name, file path, "denied", … |
| `failure_report` | Find actionable, bounded, redacted errors and failed tool calls. |
| `tool_stats` | Rank tools by volume, error rate, denials, and latency. |
| `security_audit` | Audit caller identity, tenant, server provenance, risk, and approval evidence. |
| `recent_activity` | Poll new spans with a cursor while a run is active. |
| `compare_runs` | Compare selected traces for regressions across models or versions. |

Tool descriptions are written as prompts (when-to-use, not just what-it-does) — descriptions are the interface for agent-called tools.

## Example session (real fixture trace)

```
> list_runs
[{ "trace_id": "f920798dd2558fcb84f9977736432a8b", "task": "Summarize the workspace's notes…",
   "tool_calls": 4, "human_decisions": 2, "stopped_reason": "completed" }]

> approval_log
[{ "tool": "write_file", "decision": "approve", "approver": "auto", … },
 { "tool": "run_shell",  "decision": "approve", "approver": "auto", … }]
```

## Design

```
traces/*.jsonl ──┐
traces/*.json  ──┴─▶ mcp_trace.core (local query functions)
                          │
                   mcp_trace.server (MCP adapter)
                          │
                    stdio (JSON-RPC)
```

- **core/server split**: all logic is pure functions over parsed spans; the MCP layer only parses args and JSON-encodes results. Tests hit both layers.
- **trace_id prefixes**: agents fumble full 32-char hex ids; every tool accepts prefixes.
- **bounded output**: diagnostics are truncated and obvious credentials are redacted before query results leave the server.
- **honest cost totals**: `token_usage` returns `cost_known: false` and a null cost when any model span lacks a cost or marks pricing as unavailable; unknown pricing is never presented as `$0`.
- **cursor polling**: `recent_activity` makes the snapshot reader useful while a run is still writing spans.
- The demo fixture ([`examples/example_trace.jsonl`](https://github.com/abhishekash/spanhound/blob/main/examples/example_trace.jsonl)) is a *real* agent-harness run, not hand-written.

## Honest limitations

- MCP stdio transport only (Streamable HTTP plus authenticated remote access is the next transport boundary)
- live polling re-reads snapshots; it is not a push subscription
- security audit can only report identity/provenance that the trace producer records
- read-only tools; trace mutation (annotations) is roadmap
- The Python query and server modules are available as `mcp_trace`; older import and command aliases remain for existing clients.

## First-run feedback

[Tell us what happened when you tried it](https://github.com/abhishekash/spanhound/issues/new?template=first_run.yml):
your MCP client or trace producer, the question you were trying to answer, and
any missing evidence. Share a redacted excerpt when a file fails to load.

## License

[MIT](https://github.com/abhishekash/spanhound/blob/main/LICENSE)
