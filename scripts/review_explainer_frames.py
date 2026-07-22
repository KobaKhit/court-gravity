#!/usr/bin/env python3
"""Extract review frames from a rendered explainer and build a contact sheet.

Example:
    .venv\\Scripts\\python.exe scripts/review_explainer_frames.py \\
        --video data/storyboard/court_gravity_manim_draft.mp4

Writes ignored outputs under data/storyboard/review/.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CUES = ROOT / "manim_video" / "narration_cues.json"
DEFAULT_OUT = ROOT / "data" / "storyboard" / "review"


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def probe_duration(ff: str, video: Path) -> float:
    result = subprocess.run([ff, "-i", str(video)], capture_output=True, text=True)
    for line in result.stderr.splitlines():
        if "Duration:" in line:
            stamp = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = stamp.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"Could not probe duration for {video}")


def grab(ff: str, video: Path, t: float, out: Path, duration: float) -> bool:
    """Seek and grab one frame. Returns False if the timestamp is past the video."""
    if t < 0 or t >= max(0.0, duration - 0.02):
        print(f"  skip {out.name}: t={t:.2f}s beyond duration {duration:.2f}s")
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ff,
        "-y",
        "-ss",
        f"{min(t, duration - 0.05):.3f}",
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out.exists() and out.stat().st_size > 0


def contact_sheet(paths: list[Path], out: Path, cols: int = 3) -> None:
    from PIL import Image

    existing = [p for p in paths if p.exists()]
    if not existing:
        print(f"No frames for contact sheet: {out}")
        return
    images = [Image.open(p).convert("RGB") for p in existing]
    w, h = images[0].size
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), (4, 7, 11))
    for i, im in enumerate(images):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, optimize=True)
    print(f"Wrote contact sheet: {out} ({len(existing)} frames)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--cues", type=Path, default=DEFAULT_CUES)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if not args.video.exists():
        raise SystemExit(f"Missing video: {args.video}")

    cues = json.loads(args.cues.read_text(encoding="utf-8"))
    ff = ffmpeg_exe()
    duration = probe_duration(ff, args.video)
    print(f"Video duration: {duration:.2f}s")
    frames: list[Path] = []

    # Known regression timestamps from the previous broken cut, plus cue beats.
    special = [
        ("regression-basin", 100.0),
        ("regression-field", 170.0),
        ("regression-counterfactual", 220.0),
        ("font-stress-ratings", 80.0),
    ]
    for name, t in special:
        path = args.out_dir / f"{name}.png"
        if grab(ff, args.video, t, path, duration):
            frames.append(path)
            print(f"  {name} @ {t:.1f}s")

    for section in cues["sections"]:
        start = float(section["start"])
        end = float(section["end"])
        mid = 0.5 * (start + end)
        samples = [("start", start + 0.4), ("mid", mid), ("end", max(start, end - 0.6))]
        for beat in section.get("beats", [])[:2]:
            samples.append((f"beat-{beat['at']}", start + float(beat["at"])))
        for label, t in samples:
            path = args.out_dir / f"{section['id']}_{label}.png"
            if grab(ff, args.video, min(t, end - 0.05), path, duration):
                frames.append(path)

    contact_sheet(frames[:12], args.out_dir / "contact_sheet_priority.png", cols=3)
    contact_sheet(frames, args.out_dir / "contact_sheet_full.png", cols=4)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
