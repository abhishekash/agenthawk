# AgentHawk

<!-- mcp-name: io.github.abhishekash/agenthawk -->

[![CI](https://github.com/abhishekash/agenthawk/actions/workflows/ci.yml/badge.svg)](https://github.com/abhishekash/agenthawk/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AgentHawk is a small, local-first stdio MCP server for querying JSONL
OpenTelemetry spans emitted by agent runs. It exposes focused queries for
run summaries, tool failures, approvals, activity, and comparisons instead of
requiring an application-specific dashboard.

It pairs with [agent-harness](https://github.com/abhishekash/agent-harness),
but the reader is format-simple: any JSONL of OTel-shaped spans works. The
project's concrete origin was a shell-boundary regression: the harness blocked
`cat ../outside.txt`, but the old trace recorded only that `run_shell` was
called, not the returned diagnostic. AgentHawk and the harness now preserve and
query that bounded error.

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

The tools read stored traces and can poll files being written, but they do not push events or infer intent from the final answer. Start with the [installation and user guide](docs/user-guide.md), then see the [real trace fixture](examples/example_trace.jsonl) and the [tool descriptions](src/mcp_trace/server.py) for the query contract.

## Install & run

AgentHawk is the new canonical name. The legacy `abhishekash-mcp-trace` distribution and `mcp-trace` commands remain compatibility aliases for existing users.

```bash
uvx agenthawk --trace-dir ./traces
# or, for local development:
git clone https://github.com/abhishekash/agenthawk
cd agenthawk && uv pip install -e .
agenthawk --trace-dir ./traces
```

The `agenthawk` 0.2.1 release is the renamed successor to the published
[`abhishekash-mcp-trace` 0.1.1](https://pypi.org/project/abhishekash-mcp-trace/0.1.1/)
distribution. Existing clients can continue using the legacy command while
migrating.

## Client configuration

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "agent-traces": {
      "command": "uvx",
      "args": ["agenthawk", "--trace-dir", "/path/to/traces"]
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
      "args": ["agenthawk", "--trace-dir", "/path/to/traces"]
    }
  }
}
```

**agent-harness** (mounted as gated tools):

```bash
harness run "Why was my last run slow?" --mcp "uvx agenthawk --trace-dir ./traces"
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
[{ "trace_id": "f920798dd255…", "task": "Summarize the workspace's notes…",
   "tool_calls": 4, "human_decisions": 2, "stopped_reason": "completed" }]

> approval_log
[{ "tool": "write_file", "decision": "approve", "approver": "auto", … },
 { "tool": "run_shell",  "decision": "approve", "approver": "auto", … }]
```

## Design

```
traces/*.jsonl ──▶ agenthawk.core (pure query functions, zero deps)
                          │
                   agenthawk.server (thin MCPServer adapter, mcp 2.x)
                          │
                    stdio (NDJSON JSON-RPC)
```

- **core/server split**: all logic is pure functions over parsed spans; the MCP layer only parses args and JSON-encodes results. Tests hit both layers.
- **trace_id prefixes**: agents fumble full 32-char hex ids; every tool accepts prefixes.
- **bounded output**: diagnostics are truncated and obvious credentials are redacted before query results leave the server.
- **honest cost totals**: `token_usage` returns `cost_known: false` and a null cost when any producer marks pricing as unavailable; unknown pricing is never presented as `$0`.
- **cursor polling**: `recent_activity` makes the snapshot reader useful while a run is still writing spans.
- The demo fixture ([`examples/example_trace.jsonl`](examples/example_trace.jsonl)) is a *real* agent-harness run, not hand-written.

## Honest limitations

- stdio transport only (Streamable HTTP plus authenticated remote access is the next transport boundary)
- live polling re-reads snapshots; it is not a push subscription
- security audit can only report identity/provenance that the trace producer records
- read-only tools; trace mutation (annotations) is roadmap
- `mcp_trace` remains the compatibility Python import; new code should use `agenthawk`

## License

MIT
