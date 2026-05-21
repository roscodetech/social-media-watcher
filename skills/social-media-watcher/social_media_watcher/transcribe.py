"""Caption-first transcription: reuse platform subtitles, else local Whisper."""
from __future__ import annotations

import json
import re
from pathlib import Path

from social_media_watcher.download import run

_TIME_RE = re.compile(r"(\d+):(\d{2}):(\d{2})[,.](\d{3})")


def _srt_time_to_seconds(stamp: str) -> float:
    """Convert an SRT timestamp (HH:MM:SS,mmm) to float seconds."""
    match = _TIME_RE.search(stamp)
    if not match:
        return 0.0
    h, m, s, ms = (int(g) for g in match.groups())
    return h * 3600 + m * 60 + s + ms / 1000.0


def parse_srt(path: Path) -> list[dict]:
    """Parse an SRT file into [{start, end, text}, ...] segments."""
    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if not raw:
        return []
    segments: list[dict] = []
    for block in re.split(r"\n\s*\n", raw):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        time_line = next((ln for ln in lines if "-->" in ln), None)
        if time_line is None:
            continue
        start_raw, _, end_raw = time_line.partition("-->")
        text_lines = lines[lines.index(time_line) + 1:]
        text = " ".join(t.strip() for t in text_lines).strip()
        if text:
            segments.append({
                "start": _srt_time_to_seconds(start_raw),
                "end": _srt_time_to_seconds(end_raw),
                "text": text,
            })
    return segments


def segments_to_text(segments: list[dict]) -> str:
    """Join segment texts into a single transcript string."""
    return " ".join(s["text"] for s in segments).strip()


def find_caption_file(dl_dir: Path) -> Path | None:
    """Return the first .srt subtitle file yt-dlp wrote into dl_dir, if any."""
    srt_files = sorted(dl_dir.glob("*.srt"))
    return srt_files[0] if srt_files else None


def extract_audio(video: Path, audio_path: Path) -> None:
    """Extract 16 kHz mono WAV audio from the video."""
    run(["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
         str(audio_path)])


def whisper_transcribe(audio_path: Path, out_dir: Path, model: str) -> list[dict]:
    """Transcribe audio with local whisper; return [{start, end, text}, ...]."""
    run([
        "whisper", str(audio_path), "--model", model,
        "--output_format", "json", "--output_dir", str(out_dir),
        "--condition_on_previous_text", "False", "--verbose", "False",
    ])
    produced = out_dir / f"{audio_path.stem}.json"
    if not produced.exists():
        return []
    data = json.loads(produced.read_text(encoding="utf-8"))
    produced.unlink()
    return [
        {"start": s.get("start", 0.0), "end": s.get("end", 0.0),
         "text": (s.get("text") or "").strip()}
        for s in data.get("segments", []) if (s.get("text") or "").strip()
    ]


def resolve_transcript(
    dl_dir: Path, video: Path | None, out_dir: Path, model: str
) -> tuple[str, str]:
    """Produce the transcript: captions first, Whisper fallback.

    Writes transcript.txt + transcript.json into out_dir. Returns (text, source)
    where source is 'captions', 'whisper', or 'none'.
    """
    caption = find_caption_file(dl_dir)
    if caption is not None:
        segments = parse_srt(caption)
        source = "captions" if segments else "none"
    elif video is not None:
        audio_path = out_dir / "audio.wav"
        extract_audio(video, audio_path)
        segments = whisper_transcribe(audio_path, out_dir, model)
        source = "whisper" if segments else "none"
    else:
        segments, source = [], "none"

    text = segments_to_text(segments)
    (out_dir / "transcript.txt").write_text(text, encoding="utf-8")
    (out_dir / "transcript.json").write_text(
        json.dumps(segments, indent=2), encoding="utf-8"
    )
    return text, source
