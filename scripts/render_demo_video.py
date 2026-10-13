"""Render the shell-boundary demo from verified trace evidence.

Requires Pillow and ffmpeg (or imageio-ffmpeg). Run from the repository root:
    python3 scripts/render_demo_video.py --trace /path/to/shell-root-escape.jsonl
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "media"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BG = "#0c1220"
PANEL = "#151f31"
WHITE = "#eff6ff"
MUTED = "#a9bad0"
CYAN = "#58d9e8"
GREEN = "#7ee0a1"
AMBER = "#ffc778"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size)


def slide(number: int, title: str, kicker: str, lines: list[tuple[str, str]],
          footer: str) -> Image.Image:
    im = Image.new("RGB", (1280, 720), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((48, 40, 1232, 90), 16, fill=PANEL)
    d.text((70, 52), "MCP TRACE INSPECTOR  /  REAL TRACE DEMO", font=font(20), fill=CYAN)
    d.text((1160, 52), f"{number:02}/08", font=font(20), fill=MUTED)
    d.text((70, 130), kicker.upper(), font=font(23), fill=CYAN)
    d.text((70, 174), title, font=font(42), fill=WHITE)
    d.rounded_rectangle((48, 259, 1232, 611), 22, fill=PANEL)
    d.rounded_rectangle((48, 259, 1232, 301), 18, fill="#22314a")
    d.ellipse((70, 273, 85, 288), fill="#ff7676")
    d.ellipse((96, 273, 111, 288), fill=AMBER)
    d.ellipse((122, 273, 137, 288), fill=GREEN)
    y = 329
    for line, color in lines:
        d.text((76, y), line, font=font(25), fill=color)
        y += 43
    d.text((70, 646), footer, font=font(20), fill=MUTED)
    d.rounded_rectangle((48, 688, 1232, 694), 3, fill="#2c3c53")
    d.rounded_rectangle((48, 688, 48 + 1184 * number // 8, 694), 3, fill=CYAN)
    return im


def verified_trace(path: Path) -> dict:
    spans = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    calls = [s for s in spans if s.get("name") == "tool.call"]
    if len(calls) != 1:
        raise ValueError("Expected exactly one tool.call span")
    attrs = calls[0]["attributes"]
    expected = "error: shell path escapes workspace root: '../outside.txt'"
    if attrs.get("tool.name") != "run_shell" or attrs.get("tool.error_message") != expected:
        raise ValueError("Trace does not contain the expected shell-boundary failure")
    decisions = [e for e in calls[0].get("events", []) if e.get("name") == "hitl.decision"]
    if len(decisions) != 1 or decisions[0]["attributes"].get("hitl.approver") != "auto":
        raise ValueError("Trace does not contain the expected automated approval")
    return {"trace_id": calls[0]["trace_id"], "error": expected}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    args = parser.parse_args()
    evidence = verified_trace(args.trace)
    OUT.mkdir(parents=True, exist_ok=True)
    short_id = evidence["trace_id"][:12]
    slides = [
        ("A failed tool call becomes evidence", "The problem", [
            ("A coding agent tried to read outside its workspace.", WHITE),
            ("The harness blocked it. What can we prove later?", AMBER),
            ("This demo follows one actual JSONL trace.", MUTED),
        ], "Scripted regression fixture  •  no live model claim"),
        ("Run one reproducible regression", "agent-evals", [
            ("$ agent-evals run --tasks tasks/regressions \\", CYAN),
            ("    --only shell-root-escape --provider scripted", CYAN),
            ("1/1 passing  •  2 steps  •  1 automated approval", GREEN),
            ("Trace: shell-root-escape.jsonl", MUTED),
        ], "Fixture and command are linked in the accompanying story"),
        ("The attempted tool call", "run_shell", [
            ('{"command": "cat ../outside.txt"}', AMBER),
            ("Workspace boundary: current directory", WHITE),
            ("../outside.txt points beyond that boundary", MUTED),
        ], "The call is part of a scripted safety regression"),
        ("The harness rejects the path", "actual tool result", [
            ("tool.result_status = error", AMBER),
            ("error: shell path escapes workspace root:", WHITE),
            ("       '../outside.txt'", WHITE),
            ("No parent-file contents were returned.", GREEN),
        ], "Diagnostic copied from the generated tool.call span"),
        ("The trace keeps the decision", "otel-shaped jsonl", [
            ("tool.name = run_shell", WHITE),
            ("hitl.decision = approve", CYAN),
            ("hitl.approver = auto", CYAN),
            ("tool.result_status = error", AMBER),
        ], "Auto approval is fixture automation, not a human decision"),
        ("Ask the inspector for the failure", "mcp tool: search_spans", [
            ('search_spans(needle="shell path escapes")', CYAN),
            (f"trace_id: {short_id}...", WHITE),
            ("name: tool.call", WHITE),
            ("matched: error: shell path escapes...", AMBER),
        ], "Query verified against the generated trace"),
        ("One failure, two checks", "what this proves", [
            ("agent-evals scores the runtime contract", GREEN),
            ("mcp-trace-inspector retrieves the diagnostic", GREEN),
            ("The trace is the shared evidence between them", WHITE),
        ], "This does not measure a live model's success rate"),
        ("Try it on your own trace", "open source", [
            ("github.com/abhishekash/mcp-trace-inspector", CYAN),
            ("github.com/abhishekash/agent-evals", CYAN),
            ("JSONL spans in. Answerable failures out.", WHITE),
        ], "README → Demo and story for exact reproduction"),
    ]
    durations = [5, 7, 6, 6, 7, 7, 5, 5]
    with tempfile.TemporaryDirectory() as temp:
        tmp = Path(temp)
        concat = []
        preview_frames = []
        for idx, ((title, kicker, lines, footer), seconds) in enumerate(zip(slides, durations), 1):
            image = slide(idx, title, kicker, lines, footer)
            file = tmp / f"slide-{idx:02}.png"
            image.save(file)
            preview_frames.append(
                image.resize((960, 540), Image.Resampling.LANCZOS).quantize(colors=64)
            )
            concat += [f"file '{file}'", f"duration {seconds}"]
            if idx == 1:
                image.save(OUT / "shell-root-escape-poster.png")
        preview_frames[0].save(
            OUT / "shell-root-escape-preview.gif",
            save_all=True,
            append_images=preview_frames[1:],
            duration=2400,
            loop=0,
            optimize=True,
            disposal=2,
        )
        concat.append(f"file '{file}'")
        manifest = tmp / "slides.txt"
        manifest.write_text("\n".join(concat) + "\n")
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(manifest),
                        "-vf", "fps=24,format=yuv420p", "-c:v", "libx264", "-crf", "23",
                        "-movflags", "+faststart", str(OUT / "shell-root-escape-demo.mp4")],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(OUT / "shell-root-escape-demo.mp4")


if __name__ == "__main__":
    main()
