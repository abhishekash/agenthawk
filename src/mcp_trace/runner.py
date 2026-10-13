"""Run a Python program with local OpenTelemetry capture already configured."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

from .collector import create_server


def _python_command(argv: list[str], parser: argparse.ArgumentParser) -> list[str]:
    if not argv:
        parser.error("provide a Python command after --, for example: -- python agent.py")
    name = Path(argv[0]).name.lower()
    if not re.fullmatch(r"python(?:3(?:\.\d+)?)?(?:\.exe)?", name):
        parser.error("run currently supports Python commands: -- python agent.py")
    # The app and auto-instrumentation must share one environment. Use the
    # interpreter that installed SpanHound, even if a shell alias points elsewhere.
    return [sys.executable, *argv[1:]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="spanhound run",
        description="Run a Python agent with local OpenTelemetry capture",
    )
    parser.add_argument(
        "--trace-dir",
        default=os.environ.get("MCP_TRACE_DIR", "./traces"),
        help="folder for captured traces (default: $MCP_TRACE_DIR or ./traces)",
    )
    parser.add_argument(
        "--port", type=int, default=0,
        help="loopback receiver port (default: choose an available port)",
    )
    parser.add_argument("program", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    program = args.program[1:] if args.program[:1] == ["--"] else args.program
    command = _python_command(program, parser)

    instrument = Path(sys.executable).with_name(
        "opentelemetry-instrument.exe" if os.name == "nt" else "opentelemetry-instrument"
    )
    if not instrument.is_file():
        parser.error(
            "Python auto instrumentation is missing from this environment. "
            "Install SpanHound in your agent environment with: "
            "python -m pip install 'spanhound[auto]'"
        )

    trace_dir = Path(args.trace_dir).resolve()
    try:
        trace_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        server = create_server(trace_dir, args.port)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    with server:
        before = set(trace_dir.glob("otlp-*.json"))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        env = os.environ.copy()
        env.update({
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": f"http://127.0.0.1:{server.server_port}/v1/traces",
            "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL": "http/protobuf",
            "OTEL_TRACES_EXPORTER": "otlp",
            "OTEL_METRICS_EXPORTER": "none",
            "OTEL_LOGS_EXPORTER": "none",
        })
        if len(program) > 2 and program[1] == "-m":
            service_name = program[2].split(".", 1)[0]
        elif len(program) > 1 and program[1].startswith("-"):
            service_name = "python-agent"
        else:
            service_name = Path(program[1]).stem if len(program) > 1 else "python-agent"
        env.setdefault("OTEL_SERVICE_NAME", service_name)
        print(f"spanhound capturing Python traces into {trace_dir}", file=sys.stderr)
        try:
            result = subprocess.run([str(instrument), *command], env=env, check=False)
            code = result.returncode
        except KeyboardInterrupt:
            code = 130
        except OSError as exc:
            parser.error(f"could not start Python auto instrumentation: {exc}")
        finally:
            server.shutdown()
            thread.join(timeout=3)

    captured = len(set(trace_dir.glob("otlp-*.json")) - before)
    if captured:
        print(f"spanhound captured {captured} OTLP request(s). Inspect with:", file=sys.stderr)
        print(f"  spanhound --trace-dir {trace_dir} --check", file=sys.stderr)
    else:
        print(
            "spanhound captured no library spans. Install instrumentation for the "
            "libraries this program uses, or use the documented OTLP endpoint.",
            file=sys.stderr,
        )
    return 128 + abs(code) if code < 0 else code
