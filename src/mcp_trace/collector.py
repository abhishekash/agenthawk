"""Loopback-only OTLP/HTTP trace capture for local SpanHound inspection."""
from __future__ import annotations

import gzip
import io
import json
import os
import sys
import tempfile
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from google.protobuf.json_format import MessageToDict
from google.protobuf.message import DecodeError
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
    ExportTraceServiceResponse,
)

from .otlp import parse_otlp_json

MAX_REQUEST_BYTES = 8 * 1024 * 1024


class _CaptureServer(ThreadingHTTPServer):
    daemon_threads = True
    capture_dir: Path


def _decode(payload: bytes, media_type: str) -> dict[str, Any]:
    if media_type == "application/json":
        try:
            data = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid OTLP JSON: {exc}") from exc
    else:
        request = ExportTraceServiceRequest()
        try:
            request.ParseFromString(payload)
        except DecodeError as exc:
            raise ValueError("invalid OTLP protobuf") from exc
        data = MessageToDict(request)
        data.setdefault("resourceSpans", [])
        # Protobuf's generic JSON converter base64-encodes bytes fields. OTLP
        # JSON uses hex for span IDs, which is also what our trace reader uses.
        for group_data, group in zip(data["resourceSpans"], request.resource_spans):
            for scope_data, scope in zip(group_data.get("scopeSpans", []), group.scope_spans):
                for span_data, span in zip(scope_data.get("spans", []), scope.spans):
                    span_data["traceId"] = span.trace_id.hex()
                    span_data["spanId"] = span.span_id.hex()
                    if span.parent_span_id:
                        span_data["parentSpanId"] = span.parent_span_id.hex()
    parse_otlp_json(data, "<OTLP request>")
    return data


def _persist(trace_dir: Path, data: dict[str, Any]) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    final_path = trace_dir / f"otlp-{time.time_ns()}-{uuid.uuid4().hex[:8]}.json"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=trace_dir, prefix=".spanhound-", suffix=".tmp", delete=False
        ) as output:
            temporary = Path(output.name)
            json.dump(data, output, ensure_ascii=False, separators=(",", ":"))
            output.write("\n")
        os.replace(temporary, final_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class _Handler(BaseHTTPRequestHandler):
    server: _CaptureServer

    def _respond(self, status: int, body: bytes, media_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str) -> None:
        self._respond(status, json.dumps({"error": message}).encode("utf-8"))

    def do_GET(self) -> None:
        if self.path == "/health":
            self._respond(200, b'{"status":"ok"}')
        else:
            self._error(404, "not found")

    def do_POST(self) -> None:
        if self.path != "/v1/traces":
            self._error(404, "only /v1/traces is supported")
            return
        media_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if media_type not in {"application/json", "application/x-protobuf"}:
            self._error(415, "use application/json or application/x-protobuf")
            return
        if self.headers.get("Transfer-Encoding"):
            self._error(411, "send a Content-Length header")
            return
        try:
            length = int(self.headers["Content-Length"])
        except (KeyError, TypeError, ValueError):
            self._error(411, "send a valid Content-Length header")
            return
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._error(413, "trace request exceeds 8 MiB")
            return
        self.connection.settimeout(10)
        try:
            payload = self.rfile.read(length)
            if len(payload) != length:
                raise ValueError("incomplete request body")
            encoding = self.headers.get("Content-Encoding", "identity").lower()
            if encoding == "gzip":
                with gzip.GzipFile(fileobj=io.BytesIO(payload)) as stream:
                    payload = stream.read(MAX_REQUEST_BYTES + 1)
                if len(payload) > MAX_REQUEST_BYTES:
                    self._error(413, "uncompressed trace request exceeds 8 MiB")
                    return
            elif encoding != "identity":
                self._error(415, "unsupported Content-Encoding")
                return
            data = _decode(payload, media_type)
        except (EOFError, OSError, ValueError) as exc:
            self._error(400, str(exc))
            return
        try:
            if data["resourceSpans"]:
                _persist(self.server.capture_dir, data)
        except OSError:
            self._error(500, "could not write local trace file")
            return
        if media_type == "application/x-protobuf":
            self._respond(200, ExportTraceServiceResponse().SerializeToString(), media_type)
        else:
            self._respond(200, b"{}")


def create_server(trace_dir: str | Path, port: int = 4318) -> _CaptureServer:
    """Bind a local OTLP/HTTP receiver for use by the CLI and tests."""
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    server = _CaptureServer(("127.0.0.1", port), _Handler)
    server.capture_dir = Path(trace_dir).resolve()
    return server


def serve(trace_dir: str | Path, port: int = 4318) -> None:
    """Capture OTLP/HTTP trace requests until interrupted."""
    with create_server(trace_dir, port) as server:
        print(
            f"spanhound collecting at http://127.0.0.1:{server.server_port}/v1/traces "
            f"into {server.capture_dir}",
            file=sys.stderr,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
