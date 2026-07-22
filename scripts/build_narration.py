#!/usr/bin/env python3
"""Build timed Court Gravity narration from manim_video/narration_cues.json.

Modes:
  analyze   — word budgets vs spoken/full text (no network)
  synthesize — Edge / OpenAI / ElevenLabs CLI per section → wavs
  mux       — stitch section audio onto video timeline with silence padding

Examples:
  python scripts/build_narration.py analyze
  python scripts/build_narration.py synthesize --engine elevenlabs
  python scripts/build_narration.py mux
  python scripts/build_narration.py all --engine elevenlabs --voice Daniel
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CUES = ROOT / "manim_video" / "narration_cues.json"
DEFAULT_VIDEO = ROOT / "data" / "storyboard" / "court_gravity_manim_draft.mp4"
OUT_DIR = ROOT / "data" / "storyboard" / "narration"
CLIPS_DIR = OUT_DIR / "clips"
ELEVENLABS_EXE = Path(os.environ.get("LOCALAPPDATA", "")) / "elevenlabs-cli" / "elevenlabs.exe"

# Premade voice IDs so --voice Name works even when the API key lacks voices_read.
ELEVENLABS_VOICE_IDS = {
    "daniel": "onwK4e9ZLuTAKqWW03F9",  # calm British documentary
    "adam": "pNXzCia39W387MTrQ59",  # deep American
    "george": "JBFqnCBsd6RMkjVDRZzb",  # warm British
    "brian": "nPczCjzI2devNBz1zQrb",
    "charlie": "IKne3meq5aG2GDV6lBQh",
    "callum": "N2lVS1w4EtoT3dr4eOWO",
    "bill": "pqHfZKP75CvOlQylNhV4",
    "chris": "iP95p4xoKVk53GoZ742B",
    "will": "bIHbv24MWmeRgasZH58o",
}


def load_cues(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def section_budget(section: dict, cues: dict) -> dict:
    duration = float(section["end"]) - float(section["start"])
    wpm = float(cues.get("target_wpm", 145))
    speakable = float(cues.get("speakable_fraction", 0.78))
    budget_words = duration * speakable * (wpm / 60.0)
    spoken = section.get("spoken", "")
    full = section.get("full_text", "")
    spoken_n = word_count(spoken)
    full_n = word_count(full)
    spoken_s = (spoken_n / wpm) * 60.0 if wpm else 0.0
    return {
        "id": section["id"],
        "duration_s": round(duration, 2),
        "budget_words": round(budget_words, 1),
        "spoken_words": spoken_n,
        "spoken_est_s": round(spoken_s, 2),
        "spoken_slack_s": round(duration - spoken_s, 2),
        "spoken_ok": spoken_s <= duration - 0.25,
        "full_words": full_n,
        "full_est_s": round((full_n / wpm) * 60.0, 2) if wpm else 0.0,
        "full_ok": False,
    }


def analyze(cues: dict) -> int:
    rows = [section_budget(s, cues) for s in cues["sections"]]
    print(f"target video: {cues.get('video_target_s')}s @ {cues.get('target_wpm')} wpm")
    print(f"speakable fraction: {cues.get('speakable_fraction')}")
    print()
    print(f"{'section':<28} {'dur':>6} {'budget':>7} {'spoken':>7} {'est_s':>7} {'slack':>7} {'ok':>4}  {'full_w':>6} {'full_s':>7}")
    print("-" * 100)
    bad = 0
    for r in rows:
        ok = "yes" if r["spoken_ok"] else "NO"
        if not r["spoken_ok"]:
            bad += 1
        print(
            f"{r['id']:<28} {r['duration_s']:>6.1f} {r['budget_words']:>7.1f} "
            f"{r['spoken_words']:>7d} {r['spoken_est_s']:>7.1f} {r['spoken_slack_s']:>7.1f} {ok:>4}  "
            f"{r['full_words']:>6d} {r['full_est_s']:>7.1f}"
        )
    total_spoken = sum(r["spoken_words"] for r in rows)
    total_full = sum(r["full_words"] for r in rows)
    total_dur = sum(r["duration_s"] for r in rows)
    print("-" * 100)
    print(f"spoken total: {total_spoken} words (~{total_spoken / cues['target_wpm'] * 60:.1f}s speech)")
    print(f"full_text total: {total_full} words (~{total_full / cues['target_wpm'] * 60:.1f}s — too long for {total_dur:.0f}s video)")
    if bad:
        print(f"\n{bad} section(s) may overrun. Trim spoken text or slow the scene waits.")
        return 1
    print("\nAll spoken sections fit their Manim windows (with small silence padding).")
    return 0


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "imageio-ffmpeg is required. Install with: pip install -e \".[preview]\""
        ) from exc


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def ensure_dirs() -> None:
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)


async def edge_tts_section(text: str, out_mp3: Path, voice: str, rate: str) -> None:
    try:
        import edge_tts
    except ImportError as exc:
        raise SystemExit("edge-tts is required. Install with: pip install edge-tts") from exc

    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(str(out_mp3))


def openai_tts_section(text: str, out_mp3: Path, voice: str, model: str) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")
    try:
        from urllib import request
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("urllib unavailable") from exc

    payload = json.dumps(
        {
            "model": model,
            "voice": voice,
            "input": text,
            "response_format": "mp3",
        }
    ).encode("utf-8")
    req = request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req) as resp:
        out_mp3.write_bytes(resp.read())


def mp3_to_wav(mp3: Path, wav: Path) -> None:
    ff = ffmpeg_exe()
    subprocess.run(
        [ff, "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100", str(wav)],
        check=True,
        capture_output=True,
    )


def fit_wav_to_window(wav: Path, window_s: float, *, margin: float = 0.12) -> float:
    """If wav is longer than window, time-stretch with atempo to fit (keeps pitch)."""
    dur = wav_duration(wav)
    target = max(0.25, window_s - margin)
    if dur <= window_s + 0.05:
        return dur
    tempo = min(2.0, max(0.5, dur / target))
    # atempo only accepts 0.5–2.0; chain if needed (not expected here).
    tmp = wav.with_suffix(".fit.wav")
    ff = ffmpeg_exe()
    subprocess.run(
        [
            ff,
            "-y",
            "-i",
            str(wav),
            "-filter:a",
            f"atempo={tempo:.5f}",
            "-ac",
            "1",
            "-ar",
            "44100",
            str(tmp),
        ],
        check=True,
        capture_output=True,
    )
    tmp.replace(wav)
    return wav_duration(wav)


def elevenlabs_cli() -> str:
    candidates = [
        shutil.which("elevenlabs"),
        shutil.which("elevenlabs.exe"),
        str(ELEVENLABS_EXE) if ELEVENLABS_EXE.exists() else None,
    ]
    for path in candidates:
        if path:
            return path
    raise SystemExit(
        "ElevenLabs CLI not found. Expected at %LOCALAPPDATA%\\elevenlabs-cli\\elevenlabs.exe"
    )


def resolve_elevenlabs_voice(voice: str) -> tuple[str, str]:
    """Return ('voice'|'voice-id', value) for the ElevenLabs CLI."""
    raw = voice.strip()
    lower = raw.lower()
    if lower in ELEVENLABS_VOICE_IDS:
        return "voice-id", ELEVENLABS_VOICE_IDS[lower]
    # Heuristic: ElevenLabs voice IDs are opaque alphanumeric strings.
    if re.fullmatch(r"[A-Za-z0-9]{16,}", raw):
        return "voice-id", raw
    return "voice", raw


def elevenlabs_tts_section(
    text: str,
    out_mp3: Path,
    *,
    voice: str,
    model: str,
    speed: float,
    stability: float,
    similarity: float,
    style: float,
    previous_text: str | None = None,
    next_text: str | None = None,
) -> None:
    flag, value = resolve_elevenlabs_voice(voice)
    cmd = [
        elevenlabs_cli(),
        "tts",
        text,
        f"--{flag}",
        value,
        "--model",
        model,
        "--format",
        "mp3_44100_128",
        "--stability",
        str(stability),
        "--similarity",
        str(similarity),
        "--style",
        str(style),
        "--speed",
        str(speed),
        "--speaker-boost",
        "true",
        "--language",
        "en",
        "--output",
        str(out_mp3),
        "--quiet",
    ]
    if previous_text:
        cmd.extend(["--previous-text", previous_text[:500]])
    if next_text:
        cmd.extend(["--next-text", next_text[:500]])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise SystemExit(f"ElevenLabs TTS failed for {out_mp3.name}: {err}")


def synthesize(
    cues: dict,
    *,
    engine: str,
    voice: str,
    rate: str,
    openai_model: str,
    eleven_model: str = "eleven_multilingual_v2",
    eleven_speed: float = 0.95,
    eleven_stability: float = 0.58,
    eleven_similarity: float = 0.82,
    eleven_style: float = 0.12,
    reuse_clips: bool = False,
) -> int:
    ensure_dirs()
    sections = cues["sections"]
    print(f"Synthesizing {len(sections)} sections with {engine} ({voice})...")
    if reuse_clips:
        print("  --reuse-clips: keeping existing .mp3 source files when present")

    async def run_all_edge() -> None:
        for section in sections:
            sid = section["id"]
            mp3 = CLIPS_DIR / f"{sid}.mp3"
            wav = CLIPS_DIR / f"{sid}.wav"
            text = section["spoken"].strip()
            if reuse_clips and mp3.exists():
                print(f"  {sid} (reuse mp3)")
                mp3_to_wav(mp3, wav)
                continue
            print(f"  {sid}")
            await edge_tts_section(text, mp3, voice=voice, rate=rate)
            mp3_to_wav(mp3, wav)

    if engine == "edge":
        asyncio.run(run_all_edge())
    elif engine == "openai":
        for section in sections:
            sid = section["id"]
            mp3 = CLIPS_DIR / f"{sid}.mp3"
            wav = CLIPS_DIR / f"{sid}.wav"
            if reuse_clips and mp3.exists():
                print(f"  {sid} (reuse mp3)")
                mp3_to_wav(mp3, wav)
                continue
            print(f"  {sid}")
            openai_tts_section(section["spoken"].strip(), mp3, voice=voice, model=openai_model)
            mp3_to_wav(mp3, wav)
    elif engine == "elevenlabs":
        for i, section in enumerate(sections):
            sid = section["id"]
            mp3 = CLIPS_DIR / f"{sid}.mp3"
            wav = CLIPS_DIR / f"{sid}.wav"
            text = section["spoken"].strip()
            if reuse_clips and mp3.exists():
                print(f"  {sid} (reuse mp3)")
                mp3_to_wav(mp3, wav)
                continue
            prev = sections[i - 1]["spoken"].strip() if i > 0 else None
            nxt = sections[i + 1]["spoken"].strip() if i + 1 < len(sections) else None
            print(f"  {sid}")
            elevenlabs_tts_section(
                text,
                mp3,
                voice=voice,
                model=eleven_model,
                speed=eleven_speed,
                stability=eleven_stability,
                similarity=eleven_similarity,
                style=eleven_style,
                previous_text=prev,
                next_text=nxt,
            )
            mp3_to_wav(mp3, wav)
    else:
        raise SystemExit(f"Unknown engine: {engine}")

    # fit report after synthesis
    print("\nMeasured clip lengths:")
    stretched = 0
    for section in sections:
        wav = CLIPS_DIR / f"{section['id']}.wav"
        window = float(section["end"]) - float(section["start"])
        before = wav_duration(wav)
        after = fit_wav_to_window(wav, window)
        slack = window - after
        flag = "ok"
        if after < before - 0.05:
            stretched += 1
            flag = f"fit({before:.2f}->{after:.2f})"
        print(
            f"  {section['id']:<28} audio={after:6.2f}s  window={window:6.2f}s  "
            f"slack={slack:6.2f}s  {flag}"
        )
    if stretched:
        print(f"\nTime-stretched {stretched} clip(s) to fit Manim windows (pitch preserved).")
    print("\nAll clips fit. Next: python scripts/build_narration.py mux")
    return 0


def write_silence_wav(path: Path, seconds: float, *, rate: int = 44100) -> None:
    n = max(0, int(seconds * rate))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"\x00\x00" * n)


def concat_wavs(paths: list[Path], out: Path) -> None:
    """Concatenate mono 16-bit 44.1k wavs."""
    if not paths:
        raise ValueError("no wavs to concat")
    with wave.open(str(paths[0]), "rb") as first:
        params = first.getparams()
        frames = [first.readframes(first.getnframes())]
    for path in paths[1:]:
        with wave.open(str(path), "rb") as wf:
            if wf.getparams()[:3] != params[:3]:
                raise ValueError(f"format mismatch: {path}")
            frames.append(wf.readframes(wf.getnframes()))
    with wave.open(str(out), "wb") as out_wf:
        out_wf.setparams(params)
        for chunk in frames:
            out_wf.writeframes(chunk)


def stitch_timeline(cues: dict) -> Path:
    """Place each section clip at its start time; pad with silence; trim/pad to video_target_s."""
    ensure_dirs()
    target = float(cues.get("video_target_s", cues["sections"][-1]["end"]))
    pieces: list[Path] = []
    cursor = 0.0
    tmp_dir = OUT_DIR / "_tmp_pad"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)

    for i, section in enumerate(cues["sections"]):
        start = float(section["start"])
        end = float(section["end"])
        wav = CLIPS_DIR / f"{section['id']}.wav"
        if not wav.exists():
            raise SystemExit(f"Missing clip {wav}. Run synthesize first.")
        audio_dur = wav_duration(wav)
        if start > cursor + 1e-3:
            pad = tmp_dir / f"pad_pre_{i:02d}.wav"
            write_silence_wav(pad, start - cursor)
            pieces.append(pad)
            cursor = start
        if audio_dur > (end - start) + 0.05:
            print(
                f"warning: {section['id']} audio {audio_dur:.2f}s exceeds window "
                f"{end - start:.2f}s — will overlap next section"
            )
        pieces.append(wav)
        cursor = start + audio_dur
        # pad remainder of section so next clip lands on schedule
        if end > cursor + 1e-3:
            pad = tmp_dir / f"pad_post_{i:02d}.wav"
            write_silence_wav(pad, end - cursor)
            pieces.append(pad)
            cursor = end

    if target > cursor + 1e-3:
        pad = tmp_dir / "pad_tail.wav"
        write_silence_wav(pad, target - cursor)
        pieces.append(pad)
        cursor = target

    out_wav = OUT_DIR / "court_gravity_narration.wav"
    concat_wavs(pieces, out_wav)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"Wrote {out_wav} ({cursor:.2f}s timeline)")
    return out_wav


def probe_duration(ff: str, path: Path) -> float:
    cmd = [
        ff,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    # Prefer ffprobe when bundled next to ffmpeg; fall back to parsing ffmpeg -i.
    probe = Path(ff).with_name(Path(ff).name.replace("ffmpeg", "ffprobe"))
    if "ffmpeg" in Path(ff).name.lower() and probe.exists():
        out = subprocess.check_output([str(probe), *cmd[1:]], text=True).strip()
        return float(out)
    result = subprocess.run([ff, "-i", str(path)], capture_output=True, text=True)
    for line in result.stderr.splitlines():
        if "Duration:" in line:
            # Duration: HH:MM:SS.xx,
            stamp = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = stamp.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"Could not probe duration for {path}")


def mux(cues: dict, video: Path, out_video: Path | None = None) -> Path:
    narration = stitch_timeline(cues)
    if out_video is None:
        out_video = OUT_DIR / "court_gravity_with_narration.mp4"
    if not video.exists():
        raise SystemExit(f"Video not found: {video}")
    ff = ffmpeg_exe()
    target = float(cues.get("video_target_s", cues["sections"][-1]["end"]))
    video_dur = probe_duration(ff, video)
    # If the silent render is short, freeze the last frame so A/V hit the target
    # instead of truncating narration with -shortest.
    work_video = video
    padded = OUT_DIR / "_tmp_video_pad.mp4"
    if video_dur + 0.05 < target:
        pad_s = target - video_dur
        print(f"Video is {video_dur:.2f}s; freezing last frame for {pad_s:.2f}s to reach {target:.2f}s")
        pad_cmd = [
            ff,
            "-y",
            "-i",
            str(video),
            "-vf",
            f"tpad=stop_mode=clone:stop_duration={pad_s:.3f}",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(padded),
        ]
        subprocess.run(pad_cmd, check=True, capture_output=True)
        work_video = padded
    # Replace any existing audio; keep video stream; exact target length.
    cmd = [
        ff,
        "-y",
        "-i",
        str(work_video),
        "-i",
        str(narration),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-t",
        f"{target:.3f}",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        str(out_video),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    if padded.exists():
        padded.unlink(missing_ok=True)
    # Remove ephemeral probe / padding leftovers if present.
    probe = CLIPS_DIR / "_probe.mp3"
    if probe.exists():
        probe.unlink()
    tmp_dir = OUT_DIR / "_tmp_pad"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"Muxed -> {out_video}")
    return out_video


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["analyze", "synthesize", "mux", "all"])
    parser.add_argument("--cues", type=Path, default=DEFAULT_CUES)
    parser.add_argument("--video", type=Path, default=DEFAULT_VIDEO)
    parser.add_argument("--engine", choices=["edge", "openai", "elevenlabs"], default="edge")
    parser.add_argument(
        "--voice",
        default=None,
        help="Voice name/id. Defaults: Andrew (edge), verse (openai), Daniel (elevenlabs)",
    )
    parser.add_argument("--rate", default="-5%", help="Edge TTS rate, e.g. +5%% or -10%%")
    parser.add_argument("--openai-model", default="gpt-4o-mini-tts")
    parser.add_argument("--eleven-model", default="eleven_multilingual_v2")
    parser.add_argument("--eleven-speed", type=float, default=0.95)
    parser.add_argument("--eleven-stability", type=float, default=0.58)
    parser.add_argument("--eleven-similarity", type=float, default=0.82)
    parser.add_argument("--eleven-style", type=float, default=0.12)
    parser.add_argument(
        "--reuse-clips",
        action="store_true",
        help="Reuse existing section .mp3 files (no re-TTS); remake fitted .wav only",
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.voice is None:
        args.voice = {
            "edge": "en-US-AndrewNeural",
            "openai": "verse",
            "elevenlabs": "Daniel",
        }[args.engine]

    synth_kwargs = dict(
        engine=args.engine,
        voice=args.voice,
        rate=args.rate,
        openai_model=args.openai_model,
        eleven_model=args.eleven_model,
        eleven_speed=args.eleven_speed,
        eleven_stability=args.eleven_stability,
        eleven_similarity=args.eleven_similarity,
        eleven_style=args.eleven_style,
        reuse_clips=args.reuse_clips,
    )

    cues = load_cues(args.cues)

    if args.command == "analyze":
        return analyze(cues)
    if args.command == "synthesize":
        return synthesize(cues, **synth_kwargs)
    if args.command == "mux":
        mux(cues, args.video, args.out)
        return 0
    if args.command == "all":
        code = analyze(cues)
        if code != 0:
            print("Continuing despite analyze warnings...")
        code = synthesize(cues, **synth_kwargs)
        if code != 0:
            return code
        mux(cues, args.video, args.out)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
