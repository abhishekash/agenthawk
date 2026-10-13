"""Exercise OTLP/HTTP capture through the same endpoint an SDK exporter uses."""
import gzip
import http.client
import json
import threading
from pathlib import Path

import pytest
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

from mcp_trace import core
from mcp_trace.collector import MAX_REQUEST_BYTES, create_server


@pytest.fixture
def collector(tmp_path):
    trace_dir = tmp_path / "captured"
    with create_server(trace_dir, port=0) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server.server_port, trace_dir
        finally:
            server.shutdown()
            thread.join(timeout=3)


def _request(port, body, media_type="application/json", **headers):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request("POST", "/v1/traces", body=body, headers={"Content-Type": media_type, **headers})
        response = connection.getresponse()
        return response.status, response.getheader("Content-Type"), response.read()
    finally:
        connection.close()


def test_json_export_is_saved_and_queryable(collector):
    port, trace_dir = collector
    payload = Path("tests/fixtures/otlp_trace.json").read_bytes()
    status, media_type, response = _request(port, payload)
    assert (status, media_type, response) == (200, "application/json", b"{}")
    stored = list(trace_dir.glob("*.json"))
    assert len(stored) == 1
    assert stored[0].stat().st_mode & 0o077 == 0
    spans = core.load_trace_dir(trace_dir)
    assert len(spans) == 3
    assert core.list_runs(spans)[0]["model"] == "gpt-4.1"


def test_protobuf_export_and_gzip_are_saved_as_otlp_json(collector):
    port, trace_dir = collector
    request = ExportTraceServiceRequest()
    span = request.resource_spans.add().scope_spans.add().spans.add()
    span.trace_id = bytes.fromhex("1234567890abcdef1234567890abcdef")
    span.span_id = bytes.fromhex("1234567890abcdef")
    span.name = "agent.run"
    span.start_time_unix_nano = 100
    span.end_time_unix_nano = 200
    status, media_type, response = _request(
        port,
        gzip.compress(request.SerializeToString()),
        "application/x-protobuf",
        **{"Content-Encoding": "gzip"},
    )
    assert (status, media_type, response) == (200, "application/x-protobuf", b"")
    stored = list(trace_dir.glob("*.json"))
    assert len(stored) == 1
    saved = json.loads(stored[0].read_text(encoding="utf-8"))
    assert saved["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["traceId"] == "1234567890abcdef1234567890abcdef"
    assert core.load_trace_dir(trace_dir)[0]["span_id"] == "1234567890abcdef"


def test_real_opentelemetry_http_exporter_can_send_agent_failure(collector):
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.trace.status import Status, StatusCode

    port, trace_dir = collector
    exporter = OTLPSpanExporter(endpoint=f"http://127.0.0.1:{port}/v1/traces")
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    with provider.get_tracer("spanhound-test").start_as_current_span("agent.run") as span:
        span.set_attribute("agent.task", "Inspect a denied shell call")
        span.set_attribute("tool.name", "run_shell")
        span.set_attribute("tool.result_status", "error")
        span.set_attribute("tool.error_message", "shell path escapes workspace root")
        span.set_status(Status(StatusCode.ERROR))
    provider.shutdown()

    spans = core.load_trace_dir(trace_dir)
    assert len(spans) == 1
    assert core.failure_report(spans)[0]["detail"] == "shell path escapes workspace root"


def test_invalid_and_oversized_requests_leave_no_trace(collector):
    port, trace_dir = collector
    assert _request(port, b'{"resourceSpans":{}}')[0] == 400
    assert _request(port, b"no", "text/plain")[0] == 415
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.putrequest("POST", "/v1/traces")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(MAX_REQUEST_BYTES + 1))
        connection.endheaders()
        assert connection.getresponse().status == 413
    finally:
        connection.close()
    assert not trace_dir.exists()
