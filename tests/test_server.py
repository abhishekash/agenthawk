"""Server-level tests: tools callable via the FastMCP app's tool manager."""
import json
import subprocess
import sys
from importlib.metadata import distribution

import pytest

import mcp_trace.server as server


def test_distribution_exposes_repository_named_command():
    package = distribution("spanhound")
    scripts = {ep.name: ep.value for ep in package.entry_points if ep.group == "console_scripts"}
    assert scripts["spanhound"] == "mcp_trace.server:main"
    assert scripts["mcp-trace-inspector"] == scripts["spanhound"]
    assert scripts["agenthawk"] == scripts["spanhound"]


def test_check_command_reports_example_runs():
    result = subprocess.run(
        [sys.executable, "-m", "mcp_trace", "--trace-dir", "examples", "--check"],
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(result.stdout)
    assert report["spans"] > 0
    assert report["runs"][0]["trace_id"]


def test_demo_command_shows_recorded_failure_without_trace_directory(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "mcp_trace", "demo"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "run_shell" in result.stdout
    assert "shell path escapes workspace root" in result.stdout
    assert "Approval: approve (auto)" in result.stdout
    assert "scripted agent-evals regression" in result.stdout
    assert result.stderr == ""


@pytest.fixture(autouse=True)
def point_at_fixtures(tmp_path):
    import shutil

    trace_dir = tmp_path / "traces"
    trace_dir.mkdir()
    shutil.copy("tests/fixtures/demo_trace.jsonl", trace_dir / "demo.jsonl")
    server._trace_dir = trace_dir
    yield


@pytest.mark.anyio
async def test_tools_registered():
    tools = await server.mcp.list_tools()
    names = {t.name for t in tools}
    assert names == {
        "list_runs",
        "run_summary",
        "span_tree",
        "slowest_spans",
        "approval_log",
        "token_usage",
        "search_spans",
        "failure_report",
        "tool_stats",
        "security_audit",
        "recent_activity",
        "compare_runs",
    }
    # descriptions should say *when* to use the tool, not just what it does
    slowest = next(t for t in tools if t.name == "slowest_spans")
    assert "slow" in slowest.description.lower()


@pytest.mark.anyio
async def test_list_runs_tool():
    result = await server.mcp.call_tool("list_runs", {"limit": 5})
    data = json.loads(result.content[0].text)
    assert len(data) == 1
    assert data[0]["model"] == "scripted"
    assert data[0]["trace_id"] == "f920798dd2558fcb84f9977736432a8b"


@pytest.mark.anyio
async def test_run_summary_accepts_prefix():
    result = await server.mcp.call_tool("run_summary", {"trace_id": "f920798d"})
    data = json.loads(result.content[0].text)
    assert data["tool_calls"] == 4


@pytest.mark.anyio
async def test_unknown_trace_errors():
    with pytest.raises(Exception):
        await server.mcp.call_tool("run_summary", {"trace_id": "deadbeef"})


@pytest.mark.anyio
async def test_ambiguous_trace_prefix_errors():
    original = (server._trace_dir / "demo.jsonl").read_text(encoding="utf-8")
    (server._trace_dir / "second.jsonl").write_text(
        original.replace("f920798dd2558fcb84f9977736432a8b", "f9200000000000000000000000000000"),
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="ambiguous"):
        await server.mcp.call_tool("run_summary", {"trace_id": "f920"})


@pytest.mark.anyio
async def test_approval_log_tool():
    result = await server.mcp.call_tool("approval_log", {})
    data = json.loads(result.content[0].text)
    assert len(data) == 2
    assert {d["tool"] for d in data} == {"write_file", "run_shell"}


@pytest.mark.anyio
async def test_span_tree_tool():
    result = await server.mcp.call_tool("span_tree", {"trace_id": "f920798d"})
    tree = json.loads(result.content[0].text)
    assert tree["name"] == "agent.run"
    assert len(tree["children"]) == 5


@pytest.mark.anyio
async def test_failure_report_tool():
    result = await server.mcp.call_tool("failure_report", {"trace_id": "f920798d"})
    assert json.loads(result.content[0].text) == []


@pytest.mark.anyio
async def test_tool_stats_and_security_audit_tools():
    stats = await server.mcp.call_tool("tool_stats", {"trace_id": "f920798d"})
    stats_data = json.loads(stats.content[0].text)
    assert len(stats_data) == 4

    audit = await server.mcp.call_tool("security_audit", {"trace_id": "f920798d"})
    audit_data = json.loads(audit.content[0].text)
    assert audit_data["missing_identity"] == 4


@pytest.mark.anyio
async def test_recent_activity_and_compare_tools():
    activity = await server.mcp.call_tool("recent_activity", {"limit": 2})
    activity_data = json.loads(activity.content[0].text)
    assert activity_data["count"] == 2
    compared = await server.mcp.call_tool(
        "compare_runs", {"trace_ids": ["f920798d", "f920798d"]}
    )
    compared_data = json.loads(compared.content[0].text)
    assert len(compared_data["runs"]) == 2
