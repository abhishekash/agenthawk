"""FastMCP stdio server: agents querying their own traces.

Tool design notes (these are prompts, not just schemas):
- every tool says *when* to use it, not just what it does
- results are compact JSON; trees are the only nested shape
- trace_dir comes from --trace-dir / MCP_TRACE_DIR / ./traces
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from importlib.resources import as_file, files
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from mcp_trace import core

mcp = MCPServer(
    "spanhound",
    instructions=(
        "Query local agent traces (JSONL spans or OTLP JSON exports). "
        "Use list_runs to see recent runs, run_summary/span_tree to inspect one, "
        "slowest_spans for latency questions, approval_log for what humans "
        "approved/denied, token_usage for cost questions, failure_report for "
        "errors, tool_stats for tool health, security_audit for identity and "
        "provenance gaps, recent_activity for incremental live polling, and "
        "compare_runs for regressions."
    ),
)

_trace_dir: Path = Path("./traces")


def _spans() -> list[dict]:
    try:
        return core.load_trace_dir(_trace_dir)
    except FileNotFoundError:
        return []


def _resolve(trace_id: str) -> list[dict]:
    spans = _spans()
    try:
        return core._resolve_trace_prefix(spans, trace_id)[1]
    except ValueError as exc:
        if str(exc).startswith("no trace matching"):
            known = ", ".join(t[:12] for t in core.group_traces(spans)) or "(none)"
            raise ToolError(f"{exc}; known prefixes: {known}") from exc
        raise ToolError(str(exc)) from exc


def _dump(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def _demo() -> None:
    """Show a recorded failure from the bundled scripted regression trace."""
    resource = files("mcp_trace").joinpath("data", "shell-root-escape.jsonl")
    with as_file(resource) as path:
        spans = core.load_spans(path)
    run = core.list_runs(spans)[0]
    failure = core.failure_report(spans)[0]
    decision = core.approval_log(spans)[0]
    print("SpanHound demo — recorded agent failure")
    print(f"Task: {run['task']}")
    print(f"Tool: {failure['tool']}")
    print(f"Failure: {failure['detail']}")
    print(f"Approval: {decision['decision']} ({decision['approver']})")
    print(f"Trace: {run['trace_id']} ({run['spans']} spans)")
    print("\nThis trace came from a scripted agent-evals regression.")
    print("Inspect your own JSONL or OTLP JSON traces with:")
    print("  uvx spanhound --trace-dir /path/to/traces --check")
    print("To capture traces from an instrumented agent, start:")
    print("  uvx spanhound collect --trace-dir ./traces")


@mcp.tool()
def list_runs(limit: int = 10) -> str:
    """List recent agent runs: task, model, duration, tool use, human decisions, cost.

    Use first to find the trace_id for deeper inspection.
    """
    runs = core.list_runs(_spans(), limit=limit)
    if not runs:
        return f"No traces found in {_trace_dir}. Point --trace-dir at your harness traces."
    return _dump(runs)


@mcp.tool()
def run_summary(trace_id: str) -> str:
    """Compact summary of one run (accepts trace_id prefix)."""
    spans = _resolve(trace_id)
    return _dump(core.run_summary(spans[0]["trace_id"], spans))


@mcp.tool()
def span_tree(trace_id: str) -> str:
    """Nested span tree of a run — the shape of what the agent did, with durations."""
    spans = _resolve(trace_id)
    return _dump(core.span_tree(spans[0]["trace_id"], spans))


@mcp.tool()
def slowest_spans(trace_id: str | None = None, k: int = 5) -> str:
    """Top-k slowest spans. Use for 'why was this run slow?'. Omit trace_id to search all runs."""
    spans = _resolve(trace_id) if trace_id else _spans()
    return _dump(core.slowest_spans(spans, k=k))


@mcp.tool()
def approval_log(trace_id: str | None = None) -> str:
    """Human-in-the-loop audit: every approval/denial/edit, who decided, and the rationale.

    Use when asked 'why did the agent get to do X?' or 'what was denied?'.
    """
    spans = _resolve(trace_id) if trace_id else _spans()
    return _dump(core.approval_log(spans))


@mcp.tool()
def token_usage(trace_id: str | None = None) -> str:
    """Token and cost totals. Omit trace_id to aggregate across all runs."""
    spans = _resolve(trace_id) if trace_id else _spans()
    return _dump(core.token_usage(spans))


@mcp.tool()
def search_spans(needle: str, trace_id: str | None = None) -> str:
    """Substring search over span names/attributes, e.g. a tool name, file path, or 'denied'."""
    spans = _resolve(trace_id) if trace_id else _spans()
    return _dump(core.search_spans(spans, needle))


@mcp.tool()
def failure_report(trace_id: str | None = None, limit: int = 20) -> str:
    """Show bounded, redacted tool/provider failures and their actionable diagnostics."""
    spans = _resolve(trace_id) if trace_id else _spans()
    return _dump(core.failure_report(spans, trace_id=None, limit=limit))


@mcp.tool()
def tool_stats(trace_id: str | None = None, tool_name: str | None = None, limit: int = 50) -> str:
    """Rank tools by errors, denials, latency, and call volume to find unhealthy integrations."""
    spans = _resolve(trace_id) if trace_id else _spans()
    return _dump(core.tool_stats(spans, trace_id=None, tool_name=tool_name, limit=limit))


@mcp.tool()
def security_audit(trace_id: str | None = None, limit: int = 100) -> str:
    """Audit caller identity, tenant, server provenance, risk, and approval evidence for tool calls."""
    spans = _resolve(trace_id) if trace_id else _spans()
    return _dump(core.security_audit(spans, trace_id=None, limit=limit))


@mcp.tool()
def recent_activity(
    cursor: str | None = None,
    trace_id: str | None = None,
    limit: int = 50,
) -> str:
    """Poll newly written spans using a cursor; useful while an agent run is still active."""
    spans = _resolve(trace_id) if trace_id else _spans()
    return _dump(core.recent_activity(spans, cursor=cursor, trace_id=None, limit=limit))


@mcp.tool()
def compare_runs(trace_ids: list[str]) -> str:
    """Compare selected trace-id prefixes for latency, cost, tokens, tools, and failures."""
    try:
        return _dump(core.compare_runs(_spans(), trace_ids))
    except ValueError as exc:
        raise ToolError(str(exc)) from exc


def main() -> None:
    global _trace_dir
    parser = argparse.ArgumentParser(description="Inspect and collect local agent traces")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("demo", "collect"),
        help="demo: inspect a bundled failure; collect: receive local OTLP/HTTP traces",
    )
    parser.add_argument(
        "--trace-dir",
        default=os.environ.get("MCP_TRACE_DIR", "./traces"),
        help="directory of JSONL spans or OTLP JSON exports (default: $MCP_TRACE_DIR or ./traces)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the trace directory and print recent run summaries, then exit",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4318,
        help="loopback OTLP/HTTP port for collect (default: 4318)",
    )
    args = parser.parse_args()
    if args.command == "demo":
        if args.check:
            parser.error("demo and --check cannot be used together")
        _demo()
        return
    _trace_dir = Path(args.trace_dir).resolve()
    if args.command == "collect":
        if args.check:
            parser.error("collect and --check cannot be used together")
        from mcp_trace.collector import serve

        try:
            serve(_trace_dir, args.port)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        return
    if args.check:
        try:
            spans = core.load_trace_dir(_trace_dir)
        except (FileNotFoundError, ValueError) as exc:
            parser.error(str(exc))
        print(_dump({"trace_dir": str(_trace_dir), "spans": len(spans), "runs": core.list_runs(spans)}))
        return
    print(f"spanhound serving traces from {_trace_dir}", file=sys.stderr)
    mcp.run(transport="stdio")
