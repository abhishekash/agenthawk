# mcp-trace-inspector user guide

mcp-trace-inspector lets an MCP client ask questions about an agent's recorded traces.
Point it at a directory of JSONL span records, connect it to an MCP client, and
ask about a run's tool calls, failures, approvals, timing, or token usage.

## What it helps with

Use mcp-trace-inspector when you want to:

- Find a slow model or tool call without reading every trace line.
- See recorded tool failures and bounded diagnostic messages.
- Review approval decisions, including denials and edited calls.
- Compare recorded latency, tokens, tool calls, and failures across runs.
- Keep traces on your own machine and query them from an MCP-capable client.

mcp-trace-inspector is a read-only trace viewer. It does not run, change, retry, or stop
the agent being observed. Live activity is returned by polling the trace files;
there is no push stream. Results describe evidence in the traces. Missing
identity or approval fields mean the producer did not record that evidence;
they do not prove a person or policy authorized an action.

## Requirements

- Python 3.11 or newer.
- An MCP client that can launch a local stdio server.
- JSONL traces in the project's OTel-shaped span format. The reader expects each
  line to contain a span with `trace_id`, `span_id`, `name`,
  `start_unix_nano`, `end_unix_nano`, `attributes`, and, where available,
  `parent_span_id`, `status`, and `events`. Tool, model, and approval details
  depend on the attributes your trace producer records.

The bundled example trace works immediately. Other producers may need an
export adapter to map their OTel export format into these JSONL span records.

## Install and start

After the new distribution is published to PyPI, `uvx` will run it without a
project checkout (see the [release status](../README.md)):

```bash
uvx --from mcp-trace-inspector==0.3.0 mcp-trace-inspector --trace-dir /absolute/path/to/traces
```

The server speaks MCP over standard input and output, so this command waits for
an MCP client. Its startup message goes to standard error. To use a different
trace directory, change `/absolute/path/to/traces` to the directory containing
your `.jsonl` files. Relative paths are resolved from the server's working
directory.

For a local development install:

```bash
git clone https://github.com/abhishekash/mcp-trace-inspector.git
cd mcp-trace-inspector
uv pip install -e .
mcp-trace-inspector --trace-dir /absolute/path/to/traces
```

You can also set `MCP_TRACE_DIR` and omit `--trace-dir`:

```bash
MCP_TRACE_DIR=/absolute/path/to/traces uvx --from mcp-trace-inspector==0.3.0 mcp-trace-inspector
```

The server is local and read-only. Connecting an MCP client gives that client
access to trace-derived information, including task text and recorded tool
diagnostics. Choose a trace directory appropriate for the client that will
query it.

## Connect an MCP client

Configure the client to launch `uvx` with the package and trace directory.
Restart or reload its MCP connections after saving the configuration.

For clients using the `mcpServers` JSON format, the entry looks like this:

```json
{
  "mcpServers": {
    "mcp-trace-inspector": {
      "command": "uvx",
      "args": [
        "--from",
        "mcp-trace-inspector==0.3.0",
        "mcp-trace-inspector",
        "--trace-dir",
        "/absolute/path/to/traces"
      ]
    }
  }
}
```

Use the configuration file and field names documented by your MCP client. For
example, clients can place MCP server entries in user-level or project-level
settings. Use an absolute trace path so the server does not depend on the
client's working directory.

With the mcp-trace-inspector repository checked out locally, run the server directly:

```json
{
  "mcpServers": {
    "mcp-trace-inspector": {
      "command": "/absolute/path/to/mcp-trace-inspector/.venv/bin/mcp-trace-inspector",
      "args": ["--trace-dir", "/absolute/path/to/traces"]
    }
  }
}
```

On Windows, use the executable path from your virtual environment, commonly
`C:\\path\\to\\mcp-trace-inspector\\.venv\\Scripts\\mcp-trace-inspector.exe`.

## First questions to ask

Start with `list_runs` to find a recent trace. It returns a shortened trace ID;
the other tools accept ID prefixes.

Try these prompts in your MCP client:

```text
List the recent runs and tell me which one had a failure.
For trace <prefix>, show the tool failures and their diagnostics.
For trace <prefix>, show each approval decision and why it was made.
For trace <prefix>, what were the three slowest spans?
Compare traces <prefix-a> and <prefix-b>. Did tokens, latency, or failures change?
```

The model chooses which tools to call. Ask for the trace IDs and returned
evidence in its answer so you can check the result against the source data.

## Tool reference

| Tool | What it returns | Useful question |
|---|---|---|
| `list_runs` | Recent run summaries with shortened trace IDs | “What ran recently?” |
| `run_summary` | Task, model, duration, calls, tokens, cost, outcome | “What happened in this run?” |
| `span_tree` | Nested spans, durations, selected attributes, event names | “What was the execution sequence?” |
| `slowest_spans` | Longest spans across runs or one trace | “Where did this run spend time?” |
| `approval_log` | Decision, approver, rationale, and whether an edit was recorded | “What did the reviewer approve or deny?” |
| `token_usage` | Token totals and cost when producer pricing is known | “How much model usage did these runs record?” |
| `search_spans` | Spans whose names or attributes contain a search phrase | “Find calls involving `write_file`.” |
| `failure_report` | Bounded, redacted errors and failed calls | “Why did this tool fail?” |
| `tool_stats` | Call volume, errors, denials, and latency by tool | “Which integration has the most errors?” |
| `security_audit` | Recorded identity, tenant, server, risk, and approval evidence | “Which provenance fields were recorded?” |
| `recent_activity` | Newly written spans after a polling cursor | “What new spans appeared?” |
| `compare_runs` | Per-run metrics and deltas from the first trace | “What changed between these runs?” |

## Connect agent-harness

mcp-trace-inspector can run as a stdio MCP server mounted by `agent-harness`:

```bash
harness run "Inspect the last run and explain its failure" \
  --mcp "uvx --from mcp-trace-inspector==0.3.0 mcp-trace-inspector --trace-dir ./traces" \
  --approve cli
```

The harness treats mounted MCP tools as execute-risk by default, so its
interactive approval mode asks before invoking them. Read the harness's MCP
and approval documentation for its current policy options.

## Troubleshooting

**The client says the server is unavailable.** Confirm that `uvx` is installed,
the package can be fetched, and the configured trace path exists. Reload the
client's MCP configuration and check its server logs; the server writes its
startup message to standard error.

**No runs appear.** Check that the path points to a directory
containing `.jsonl` files. The server searches subdirectories. The included
example is at `examples/example_trace.jsonl` in the repository.

**Runs appear, but model or approval details are missing.** The server only
reports fields present in the trace. Check whether your producer exports model
names, token counts, cost-known status, tool call spans, and approval events.
Missing fields are not inferred from the final answer.

**The JSONL is rejected.** Each line must be a JSON object representing one
span with the required trace ID, span ID, name, and start and end timestamps.
Ask your tracing exporter to produce one span object per line.

## Privacy and limits

mcp-trace-inspector processes the files in the configured directory and returns selected
trace fields to the connected MCP client. Failure messages are bounded and
credential patterns are redacted, but redaction is not a guarantee that every
private value is removed. Review trace contents and client access before using
it with sensitive data.

The current server uses local stdio transport. It polls stored files for new
spans rather than receiving push events. `security_audit` summarizes recorded
identity and provenance; it does not independently verify them. Cost totals
are unknown when the trace producer does not provide reliable pricing.

## Example data

Try mcp-trace-inspector against the checked-in
[example trace](../examples/example_trace.jsonl). It contains a run emitted by
`agent-harness` and can be queried using the tools above.

[Back to the README](../README.md)
