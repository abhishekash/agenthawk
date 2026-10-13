"""One-command Python capture from an otherwise uninstrumented program."""
import http.server
import json
import subprocess
import sys
import threading

from mcp_trace import core


class _Success(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        body = json.dumps({
            "id": "chatcmpl-local", "object": "chat.completion", "created": 1,
            "model": "local-test", "choices": [{
                "index": 0, "message": {"role": "assistant", "content": "hello"},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def test_run_captures_requests_without_app_tracing_code(tmp_path):
    script = tmp_path / "agent.py"
    script.write_text(
        "import requests, sys\nrequests.get(sys.argv[1], timeout=3).raise_for_status()\n",
        encoding="utf-8",
    )
    trace_dir = tmp_path / "traces"
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Success) as target:
        thread = threading.Thread(target=target.serve_forever, daemon=True)
        thread.start()
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "mcp_trace", "run", "--trace-dir", str(trace_dir),
                    "--", "python", str(script), f"http://127.0.0.1:{target.server_port}/ok",
                ],
                text=True, capture_output=True, timeout=20,
            )
        finally:
            target.shutdown()
            thread.join(timeout=3)
    assert result.returncode == 0, result.stderr
    assert "captured" in result.stderr
    spans = core.load_trace_dir(trace_dir)
    assert any(
        span["attributes"].get("http.request.method", span["attributes"].get("http.method")) == "GET"
        for span in spans
    )


def test_run_captures_openai_model_span_without_app_tracing_code(tmp_path):
    script = tmp_path / "agent.py"
    script.write_text(
        "from openai import OpenAI\n"
        "import sys\n"
        "client = OpenAI(api_key='test', base_url=sys.argv[1])\n"
        "client.chat.completions.create(model='local-test', messages=[{'role':'user','content':'hello'}])\n",
        encoding="utf-8",
    )
    trace_dir = tmp_path / "traces"
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Success) as target:
        thread = threading.Thread(target=target.serve_forever, daemon=True)
        thread.start()
        try:
            result = subprocess.run(
                [sys.executable, "-m", "mcp_trace", "run", "--trace-dir", str(trace_dir),
                 "--", "python", str(script), f"http://127.0.0.1:{target.server_port}/v1"],
                text=True, capture_output=True, timeout=20,
            )
        finally:
            target.shutdown()
            thread.join(timeout=3)
    assert result.returncode == 0, result.stderr
    spans = core.load_trace_dir(trace_dir)
    assert any(span["attributes"].get("gen_ai.operation.name") for span in spans)
    assert any(run["model"] == "local-test" for run in core.list_runs(spans))
    assert core.token_usage(spans)["total_tokens"] == 4


def test_run_preserves_child_exit_code_and_reports_no_spans(tmp_path):
    script = tmp_path / "exit.py"
    script.write_text("raise SystemExit(7)\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "mcp_trace", "run", "--trace-dir", str(tmp_path / "traces"),
         "--", "python", str(script)],
        text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 7
    assert "captured no library spans" in result.stderr
