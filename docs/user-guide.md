# SpanHound user guide

SpanHound lets an MCP client ask questions about an agent's recorded traces.
Point it at a directory of JSONL spans or OTLP JSON exports, connect it to an MCP client, and
ask about a run's tool calls, failures, approvals, timing, or token usage.

## What it helps with

Use spanhound when you want to:

- Find a slow model or tool call without reading every trace line.
- See recorded tool failures and bounded diagnostic messages.
- Review approval decisions, including denials and edited calls.
- Compare recorded latency, tokens, tool calls, and failures across runs.
- Keep traces on your own machine and query them from an MCP-capable client.

spanhound is a read-only trace viewer. It does not run, change, retry, or stop
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
- Or saved OTLP/JSON trace exports (`.json`) containing a `resourceSpans` array,
  as produced by an OpenTelemetry exporter or collector. The reader accepts
  both formats in the same directory and searches subdirectories.

The bundled [JSONL example](../examples/example_trace.jsonl) and
[OTLP JSON example](../tests/fixtures/otlp_trace.json) work immediately. Backend-specific
exports, such as Jaeger JSON, may need conversion to OTLP/JSON.

## Install and start

```bash
uvx spanhound --trace-dir /absolute/path/to/traces
```

The server speaks MCP over standard input and output, so this command waits for
an MCP client. Its startup message goes to standard error. To use a different
trace directory, change `/absolute/path/to/traces` to the directory containing
your `.jsonl` or OTLP `.json` files. Relative paths are resolved from the server's working
directory.

For a local development install:

```bash
git clone https://github.com/abhishekash/spanhound.git
cd spanhound
uvx --from . spanhound --trace-dir /absolute/path/to/traces
```

Run `uvx --from . spanhound --trace-dir examples --check` from the
repository to validate the included fixture and print its run summary without
starting an MCP client.

You can also set `MCP_TRACE_DIR` and omit `--trace-dir`:

```bash
MCP_TRACE_DIR=/absolute/path/to/traces uvx spanhound
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
    "spanhound": {
      "command": "uvx",
      "args": [
        "spanhound",
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

With the spanhound repository checked out locally, run the server directly:

```json
{
  "mcpServers": {
    "spanhound": {
      "command": "/absolute/path/to/spanhound/.venv/bin/spanhound",
      "args": ["--trace-dir", "/absolute/path/to/traces"]
    }
  }
}
```

On Windows, use the executable path from your virtual environment, commonly
`C:\\path\\to\\spanhound\\.venv\\Scripts\\spanhound.exe`.

## First questions to ask

Start with `list_runs` to find a recent trace. It returns full trace IDs; the
other tools also accept unambiguous prefixes.

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
| `list_runs` | Recent run summaries with full trace IDs | “What ran recently?” |
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

spanhound can run as a stdio MCP server mounted by `agent-harness`:

```bash
harness run "Inspect the last run and explain its failure" \
  --mcp "uvx spanhound --trace-dir ./traces" \
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

**No runs appear.** Check that the path points to a directory containing
`.jsonl` span files or OTLP `.json` exports. The server searches subdirectories.
The included JSONL example is at `examples/example_trace.jsonl`.

**Runs appear, but model or approval details are missing.** The server only
reports fields present in the trace. Check whether your producer exports model
names, token counts, cost-known status, tool call spans, and approval events.
Missing fields are not inferred from the final answer.

**The JSONL is rejected.** Each line must be a JSON object representing one
span with the required trace ID, span ID, name, and start and end timestamps.
Ask your tracing exporter to produce one span object per line.

**The OTLP JSON is rejected.** Export an OTLP/JSON trace request with
`resourceSpans`, `scopeSpans`, and `spans`; a Jaeger or Zipkin API response is
a different format. `--check` reports the file and invalid field.

**A trace ID prefix is ambiguous.** Copy the full ID from `list_runs` or use a
longer prefix. The server will report ambiguity instead of mixing runs.

## Privacy and limits

spanhound processes the files in the configured directory and returns selected
trace fields to the connected MCP client. Failure messages are bounded and
credential patterns are redacted, but redaction is not a guarantee that every
private value is removed. Review trace contents and client access before using
it with sensitive data.

The current server uses local stdio transport. It polls stored files for new
spans rather than receiving push events. `security_audit` summarizes recorded
identity and provenance; it does not independently verify them. Cost totals
are unknown when the trace producer does not provide reliable pricing.

## Example data

Try spanhound against the checked-in
[example trace](../examples/example_trace.jsonl). It contains a run emitted by
`agent-harness` and can be queried using the tools above.

[Back to the README](../README.md)
