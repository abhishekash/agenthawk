"""Core query tests against agent-harness and OTLP trace fixtures."""
import json
from pathlib import Path

import pytest

from mcp_trace import core

TRACE_ID = "f920798dd2558fcb84f9977736432a8b"


@pytest.fixture(scope="module")
def spans():
    return core.load_spans("tests/fixtures/demo_trace.jsonl")


@pytest.fixture(scope="module")
def trace_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("traces")
    import shutil

    shutil.copy("tests/fixtures/demo_trace.jsonl", d / "demo.jsonl")
    return d


class TestLoading:
    def test_load_spans(self, spans):
        assert len(spans) == 15
        assert {s["trace_id"] for s in spans} == {TRACE_ID}

    def test_load_trace_dir(self, trace_dir):
        assert len(core.load_trace_dir(trace_dir)) == 15

    def test_load_trace_dir_recursive(self, trace_dir):
        nested = trace_dir / "2026" / "04"
        nested.mkdir(parents=True)
        import shutil

        shutil.copy("tests/fixtures/demo_trace.jsonl", nested / "nested.jsonl")
        assert len(core.load_trace_dir(trace_dir)) == 30

    def test_missing_dir(self):
        with pytest.raises(FileNotFoundError):
            core.load_trace_dir("/nope/not-here")

    def test_group_traces_sorted(self, spans):
        traces = core.group_traces(spans)
        starts = [s["start_unix_nano"] for s in traces[TRACE_ID]]
        assert starts == sorted(starts)

    def test_partial_final_line_does_not_hide_completed_spans(self, trace_dir):
        path = trace_dir / "writing.jsonl"
        path.write_text('{"trace_id":"complete"}\n{"trace_id":', encoding="utf-8")
        assert [span["trace_id"] for span in core.load_spans(path)] == ["complete"]

    def test_malformed_complete_line_is_reported(self, trace_dir):
        path = trace_dir / "broken.jsonl"
        path.write_text('{"trace_id":}\n', encoding="utf-8")
        with pytest.raises(ValueError, match="invalid span JSON"):
            core.load_spans(path)

    def test_otlp_export_queries_and_jsonl_coexist(self, tmp_path):
        import shutil

        shutil.copy("tests/fixtures/demo_trace.jsonl", tmp_path / "demo.jsonl")
        shutil.copy("tests/fixtures/otlp_trace.json", tmp_path / "export.json")
        loaded = core.load_trace_dir(tmp_path)
        assert len(loaded) == 18
        assert len(core.list_runs(loaded)) == 2
        otlp = [span for span in loaded if span["_source_file"].endswith("export.json")]
        assert len(otlp) == 3
        assert otlp[0]["trace_id"] == "a920798dd2558fcb84f9977736432a8b"
        assert otlp[2]["attributes"]["tool.arguments"] == {"retry": True}
        summary = core.run_summary(otlp[0]["trace_id"], otlp)
        assert summary["model"] == "gpt-4.1"
        assert summary["tool_calls"] == 1
        assert summary["tools_used"] == ["lookup"]
        assert summary["input_tokens"] == 42
        assert core.token_usage(otlp)["total_tokens"] == 49
        assert core.token_usage(otlp)["cost_usd"] is None
        assert core.span_tree(otlp[0]["trace_id"], otlp)["children"][1]["name"] == "execute_tool lookup"
        assert core.failure_report(otlp)[0]["detail"] == "Lookup unavailable"
        assert core.tool_stats(otlp)[0]["tool"] == "lookup"

    def test_otlp_export_rejects_invalid_shape_and_ids(self, tmp_path):
        path = tmp_path / "invalid.json"
        path.write_text('{"spans": []}', encoding="utf-8")
        with pytest.raises(ValueError, match="resourceSpans"):
            core.load_trace_dir(tmp_path)
        content = json.loads(Path("tests/fixtures/otlp_trace.json").read_text(encoding="utf-8"))
        content["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["traceId"] = "bad"
        path.write_text(json.dumps(content), encoding="utf-8")
        with pytest.raises(ValueError, match="traceId must be"):
            core.load_trace_dir(tmp_path)


class TestRunSummary:
    def test_summary_fields(self, spans):
        s = core.run_summary(TRACE_ID, spans)
        assert s["task"].startswith("Summarize the workspace's notes")
        assert s["model"] == "scripted"
        assert s["tool_calls"] == 4
        assert s["tools_used"] == ["list_dir", "read_file", "run_shell", "write_file"]
        assert s["human_decisions"] == 2
        assert s["denials"] == 0
        assert s["stopped_reason"] == "completed"

    def test_list_runs(self, spans):
        runs = core.list_runs(spans)
        assert len(runs) == 1
        assert runs[0]["trace_id"] == TRACE_ID


class TestSpanTree:
    def test_shape(self, spans):
        tree = core.span_tree(TRACE_ID, spans)
        assert tree["name"] == "agent.run"
        steps = tree["children"]
        assert len(steps) == 5
        assert all(s["name"] == "agent.step" for s in steps)
        # step 3 holds the write_file call with its hitl event
        step3_children = steps[2]["children"]
        tool_span = next(c for c in step3_children if c["name"] == "tool.call")
        assert tool_span["attributes"]["tool.name"] == "write_file"
        assert "hitl.decision" in tool_span["events"]


class TestSlowest:
    def test_slowest_first(self, spans):
        top = core.slowest_spans(spans, k=2)
        assert top[0]["name"] == "agent.run"
        assert top[0]["duration_ms"] >= top[1]["duration_ms"]

    def test_filter_by_name(self, spans):
        top = core.slowest_spans(spans, k=5, name_filter="tool")
        assert all("tool" in t["name"] for t in top)
        assert top[0]["tool"] == "run_shell"  # the slowest tool call in the demo


class TestApprovalLog:
    def test_decisions_extracted(self, spans):
        log = core.approval_log(spans)
        assert len(log) == 2
        assert {entry["tool"] for entry in log} == {"write_file", "run_shell"}
        assert all(entry["decision"] == "approve" for entry in log)
        assert all(entry["approver"] == "auto" for entry in log)


class TestTokenUsage:
    def test_aggregation(self, spans):
        usage = core.token_usage(spans)
        assert usage["llm_calls"] == 5
        assert usage["input_tokens"] == 92 + 94 + 125 + 132 + 196
        assert usage["output_tokens"] > 0
        assert usage["cost_known"] is True

    def test_unknown_cost_is_not_reported_as_zero(self, spans):
        unknown = dict(spans[0])
        unknown["attributes"] = dict(unknown["attributes"])
        unknown["attributes"]["llm.cost_known"] = False
        usage = core.token_usage([unknown])
        assert usage["cost_known"] is False
        assert usage["cost_usd"] is None

    def test_missing_cost_is_unknown(self, spans):
        llm = next(span for span in spans if span["name"] == "llm.complete")
        without_cost = {**llm, "attributes": dict(llm["attributes"])}
        without_cost["attributes"].pop("llm.cost_usd")
        usage = core.token_usage([without_cost])
        assert usage["cost_known"] is False
        assert usage["cost_usd"] is None


class TestNewQueries:
    def test_failure_report_is_bounded_and_redacted(self, spans):
        failed = dict(spans[1])
        failed["attributes"] = {
            **failed["attributes"],
            "tool.result_status": "error",
            "tool.error_message": "authorization: Bearer sk-12345678901234567890",
        }
        report = core.failure_report(spans + [failed], limit=1)
        assert len(report) == 1
        assert report[0]["result_status"] == "error"
        assert "sk-123" not in report[0]["detail"]
        assert "<redacted>" in report[0]["detail"]

    def test_tool_stats(self, spans):
        stats = core.tool_stats(spans)
        assert len(stats) == 4
        shell = next(row for row in stats if row["tool"] == "run_shell")
        assert shell["calls"] == 1
        assert shell["errors"] == 0
        assert shell["p95_duration_ms"] > 0

    def test_security_audit_flags_missing_provenance(self, spans):
        audit = core.security_audit(spans)
        assert audit["calls"] == 4
        assert audit["missing_identity"] == 4
        assert audit["missing_server_provenance"] == 4
        assert audit["records"][0]["identity"] is None

    def test_recent_activity_uses_cursor(self, spans):
        first = core.recent_activity(spans, limit=2)
        second = core.recent_activity(spans, cursor=first["next_cursor"], limit=2)
        assert first["count"] == 2
        assert second["count"] == 2
        assert not {row["span_id"] for row in first["spans"]} & {
            row["span_id"] for row in second["spans"]
        }

    def test_compare_runs(self, spans):
        compared = core.compare_runs(spans, [TRACE_ID, TRACE_ID])
        assert len(compared["runs"]) == 2
        assert compared["runs"][1]["delta_vs_first"]["total_tokens"] == 0

    def test_compare_runs_with_unknown_cost(self, spans):
        changed = [dict(span) for span in spans]
        llm = next(span for span in changed if span["name"] == "llm.complete")
        llm["attributes"] = {**llm["attributes"], "llm.cost_known": False}
        compared = core.compare_runs(changed, [TRACE_ID])
        assert compared["runs"][0]["cost_usd"] is None
        assert compared["runs"][0]["delta_vs_first"]["cost_usd"] is None

    def test_trace_prefix_must_be_unambiguous(self, spans):
        second = [{**span, "trace_id": "f920-other"} for span in spans]
        with pytest.raises(ValueError, match="ambiguous"):
            core.compare_runs(spans + second, ["f920"])
        with pytest.raises(ValueError, match="must not be empty"):
            core.compare_runs(spans, [""])

    def test_compare_counts_failures_beyond_report_limit(self, spans):
        tool = next(span for span in spans if span["name"] == "tool.call")
        failures = [
            {
                **tool,
                "span_id": f"failed-{index}",
                "attributes": {**tool["attributes"], "tool.result_status": "error"},
            }
            for index in range(25)
        ]
        compared = core.compare_runs(spans + failures, [TRACE_ID])
        assert compared["runs"][0]["failures"] == 25


class TestSearch:
    def test_by_tool_name(self, spans):
        hits = core.search_spans(spans, "write_file")
        assert hits and all("write_file" in str(h["matched"]) for h in hits)

    def test_no_hits(self, spans):
        assert core.search_spans(spans, "definitely-not-here") == []
