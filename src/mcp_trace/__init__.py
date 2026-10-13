"""spanhound: MCP server over trace query core.

The ``mcp_trace`` import remains as a compatibility module for pre-0.2 users.
"""
from mcp_trace.core import (
    approval_log,
    compare_runs,
    failure_report,
    group_traces,
    list_runs,
    load_spans,
    load_trace_dir,
    recent_activity,
    run_summary,
    search_spans,
    security_audit,
    slowest_spans,
    span_tree,
    token_usage,
    tool_stats,
)

__version__ = "0.3.0"
__all__ = [
    "approval_log",
    "compare_runs",
    "failure_report",
    "group_traces",
    "list_runs",
    "load_spans",
    "load_trace_dir",
    "recent_activity",
    "run_summary",
    "search_spans",
    "security_audit",
    "slowest_spans",
    "span_tree",
    "token_usage",
    "tool_stats",
    "__version__",
]
