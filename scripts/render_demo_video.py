"""Render the shell-boundary demo from verified trace evidence.

Requires Pillow and ffmpeg (or imageio-ffmpeg). Run from the repository root:
    python3 scripts/render_demo_video.py --trace /path/to/shell-root-escape.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "media"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG = "#07101e"
PANEL = "#101d30"
WHITE = "#eff6ff"
MUTED = "#a9bad0"
CYAN = "#6eeaff"
GREEN = "#83f6bd"
AMBER = "#ffd28a"
CORAL = "#ff748d"
BLUE = "#378bff"


def font(size: int, *, headline: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(SANS_BOLD if headline else FONT, size)


def rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    return (*bytes.fromhex(color.lstrip("#")), alpha)


def backdrop() -> Image.Image:
    im = Image.new("RGBA", (1280, 720), BG)
    d = ImageDraw.Draw(im)
    for y in range(720):
        d.line((0, y, 1280, y), fill=(7, 15 + y // 180, 29 + y // 65, 255))
    bloom = Image.new("RGBA", im.size)
    b = ImageDraw.Draw(bloom)
    b.ellipse((720, -280, 1470, 470), fill=rgba(BLUE, 42))
    b.ellipse((-340, 370, 350, 1060), fill=rgba(CYAN, 28))
    im.alpha_composite(bloom.filter(ImageFilter.GaussianBlur(120)))
    grid_layer = Image.new("RGBA", im.size)
    grid = ImageDraw.Draw(grid_layer)
    for x in range(0, 1281, 64):
        grid.line((x, 0, x, 720), fill=rgba(CYAN, 20))
    for y in range(0, 721, 64):
        grid.line((0, y, 1280, y), fill=rgba(CYAN, 20))
    im.alpha_composite(grid_layer)
    return im


def radar(im: Image.Image, number: int, accent: str) -> None:
    ring_layer = Image.new("RGBA", im.size)
    rings = ImageDraw.Draw(ring_layer)
    cx, cy = 1052, 459
    for radius, alpha in ((142, 60), (106, 105), (70, 170)):
        rings.ellipse((cx-radius, cy-radius, cx+radius, cy+radius),
                      outline=rgba(accent, alpha), width=2)
    im.alpha_composite(ring_layer)
    d = ImageDraw.Draw(im)
    for angle in range(0, 360, 60):
        theta = math.radians(angle + number * 7)
        x = cx + int(106 * math.cos(theta))
        y = cy + int(106 * math.sin(theta))
        d.ellipse((x-5, y-5, x+5, y+5), fill=accent)
    d.line((cx-55, cy, cx-12, cy, cx+12, cy-30,
            cx+45, cy+30, cx+70, cy+30), fill=accent, width=4)
    status = "BLOCKED" if number == 4 else "TRACE / 0" + str(number)
    d.text((cx-75, cy+55), status, font=font(17), fill=accent if number == 4 else MUTED)


def slide(number: int, title: str, kicker: str, lines: list[tuple[str, str]],
          footer: str) -> Image.Image:
    im = backdrop()
    accent = CORAL if number == 4 else GREEN if number == 2 else CYAN
    halo = Image.new("RGBA", im.size)
    h = ImageDraw.Draw(halo)
    h.rounded_rectangle((48, 259, 1232, 612), 24,
                        outline=rgba(accent, 110), width=5)
    im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(im)
    d.line((48, 102, 1232, 102), fill="#365474", width=2)
    d.rounded_rectangle((48, 40, 97, 86), 10, fill="#103e4b", outline=CYAN, width=2)
    d.text((63, 47), "M", font=font(25, headline=True), fill=CYAN)
    d.text((115, 50), "MCP / TRACE INSPECTOR", font=font(19), fill=WHITE)
    d.ellipse((958, 58, 969, 69), fill=GREEN)
    d.text((981, 54), "REAL TRACE • STDIO MCP", font=font(16), fill=MUTED)
    d.rounded_rectangle((65, 126, 65 + 19 * len(kicker), 159), 10,
                        fill="#133746", outline=CYAN, width=1)
    d.text((78, 133), kicker.upper(), font=font(17), fill=CYAN)
    if number == 1:
        lead = "Make failures "
        headline_font = font(47, headline=True)
        d.text((65, 181), lead, font=headline_font, fill=WHITE)
        d.text((65 + d.textlength(lead, font=headline_font), 181),
               "answerable.", font=headline_font, fill=CYAN)
    else:
        d.text((65, 181), title, font=font(47, headline=True), fill=WHITE)
    d.rounded_rectangle((48, 259, 1232, 611), 22,
                        fill=PANEL, outline=accent, width=2)
    d.rounded_rectangle((48, 259, 1232, 307), 20, fill="#18314b")
    d.rectangle((49, 286, 1231, 308), fill="#18314b")
    for x, color in ((76, CORAL), (101, AMBER), (126, GREEN)):
        d.ellipse((x, 276, x + 14, 290), fill=color)
    d.text((170, 274), "EVIDENCE VIEW  /  SCRIPTED REGRESSION",
           font=font(17), fill=MUTED)
    d.line((859, 330, 859, 577), fill="#2e4d61", width=2)
    d.rounded_rectangle((68, 327, 74, 570), 3, fill=accent)
    y = 344
    for line, color in lines:
        d.text((94, y), line, font=font(23), fill=color)
        y += 47
    radar(im, number, accent)
    d = ImageDraw.Draw(im)
    d.line((48, 641, 1232, 641), fill="#365474", width=2)
    d.text((67, 655), footer, font=font(17), fill=MUTED)
    d.text((1138, 655), f"{number:02} / 08", font=font(16), fill=CYAN)
    return im.convert("RGB")


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


def animated_frame(slides: list[Image.Image], durations: list[int],
                   seconds: float) -> Image.Image:
    total = sum(durations)
    start = 0
    scene = len(slides) - 1
    local = 0.0
    for idx, duration in enumerate(durations):
        if seconds < start + duration:
            scene = idx
            local = seconds - start
            break
        start += duration
    accent = CORAL if scene == 3 else GREEN if scene == 1 else CYAN
    image = slides[scene].copy()
    if scene < len(slides) - 1 and local > durations[scene] - 0.65:
        amount = (local - durations[scene] + 0.65) / 0.65
        image = Image.blend(image, slides[scene + 1], amount)
    overlay = Image.new("RGBA", image.size)
    d = ImageDraw.Draw(overlay)
    sweep = seconds * 1.8
    cx, cy = 1052, 459
    x = cx + int(140 * math.cos(sweep))
    y = cy + int(140 * math.sin(sweep))
    d.line((cx, cy, x, y), fill=rgba(accent, 115), width=3)
    d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=rgba(accent, 215))
    scan_y = 320 + int((seconds * 24) % 270)
    d.line((74, scan_y, 855, scan_y), fill=rgba(CYAN, 24), width=2)
    pulse = 130 + int(85 * (0.5 + 0.5 * math.sin(seconds * 5)))
    d.ellipse((958, 58, 969, 69), fill=rgba(GREEN, pulse))
    d.rounded_rectangle((48, 695, 1232, 700), 3, fill=rgba("#344c66"))
    d.rounded_rectangle((48, 695, 48 + int(1184 * seconds / total), 700),
                        3, fill=rgba(CYAN))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def encode_video(slides: list[Image.Image], durations: list[int]) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    fps = 15
    command = [ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-s", "1280x720", "-r", str(fps),
               "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
               str(OUT / "shell-root-escape-demo.mp4")]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    try:
        assert proc.stdin is not None
        for n in range(sum(durations) * fps):
            proc.stdin.write(animated_frame(slides, durations, n / fps).tobytes())
        proc.stdin.close()
        assert proc.stderr is not None
        error = proc.stderr.read().decode(errors="replace")
        if proc.wait() != 0:
            raise RuntimeError(error[-3000:])
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def encode_preview(slides: list[Image.Image], durations: list[int]) -> None:
    frames: list[Image.Image] = []
    timing: list[int] = []
    start = 0
    for idx, duration in enumerate(durations):
        still = animated_frame(slides, durations, start + duration / 2)
        frames.append(still.resize((960, 540), Image.Resampling.LANCZOS)
                      .quantize(colors=96))
        timing.append(1600)
        if idx < len(slides) - 1:
            for amount in (0.25, 0.5, 0.75):
                blend = Image.blend(slides[idx], slides[idx + 1], amount)
                frames.append(blend.resize((960, 540), Image.Resampling.LANCZOS)
                              .quantize(colors=96))
                timing.append(120)
        start += duration
    frames[0].save(OUT / "shell-root-escape-preview.gif", save_all=True,
                   append_images=frames[1:], duration=timing, loop=0,
                   optimize=True, disposal=2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    args = parser.parse_args()
    evidence = verified_trace(args.trace)
    OUT.mkdir(parents=True, exist_ok=True)
    short_id = evidence["trace_id"][:12]
    slides = [
        ("Make failures answerable.", "Trace intelligence", [
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
    images = [slide(idx, title, kicker, lines, footer)
              for idx, (title, kicker, lines, footer) in enumerate(slides, 1)]
    images[0].save(OUT / "shell-root-escape-poster.png")
    encode_preview(images, durations)
    encode_video(images, durations)
    print(OUT / "shell-root-escape-demo.mp4")


if __name__ == "__main__":
    main()
