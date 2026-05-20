#!/usr/bin/env python3
"""tiktok_watch.py — Download a TikTok post and extract frames, audio, transcript, metadata.

Produces an artifact bundle in output/<UTC-timestamp>-<video-id>/ and prints the
output directory path as the final stdout line. Designed to be driven by the
tiktok-watcher Claude Code skill.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# --- Constants ---------------------------------------------------------------
REQUIRED_TOOLS = ("yt-dlp", "ffmpeg", "whisper")
VIDEO_ID_RE = re.compile(r"/video/(\d+)")
HASHTAG_RE = re.compile(r"#(\w+)")
SCENE_THRESHOLD = 0.3
MIN_SCENE_FRAMES = 4
DEFAULT_MAX_FRAMES = 14
DEFAULT_WHISPER_MODEL = "small"
FRAME_LONG_EDGE = 720
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


# --- URL handling ------------------------------------------------------------
def is_tiktok_url(url: str) -> bool:
    """Return True if url is an http(s) URL whose host is on tiktok.com."""
    try:
        parsed = urlparse((url or "").strip())
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.netloc.lower().split(":")[0]
    return host == "tiktok.com" or host.endswith(".tiktok.com")


def extract_video_id(url: str) -> str | None:
    """Extract the numeric video id from a full TikTok URL, or None for short links."""
    match = VIDEO_ID_RE.search(url or "")
    return match.group(1) if match else None


def looks_like_single_post(url: str) -> bool:
    """Return True if the URL points to one post, not a profile or feed."""
    parsed = urlparse((url or "").strip())
    host = parsed.netloc.lower().split(":")[0]
    path = parsed.path
    if host in ("vm.tiktok.com", "vt.tiktok.com"):
        return True
    return "/video/" in path or "/photo/" in path or path.startswith("/t/")


def validate_url(url: str) -> str:
    """Return the trimmed URL if it is a single-post TikTok URL, else raise ValueError."""
    cleaned = (url or "").strip()
    if not is_tiktok_url(cleaned):
        raise ValueError(f"Not a TikTok URL: {url!r}")
    if not looks_like_single_post(cleaned):
        raise ValueError(
            f"URL does not point to a single TikTok post (looks like a profile or feed): {url!r}"
        )
    return cleaned


# --- Metadata ----------------------------------------------------------------
def extract_hashtags(text: str) -> list[str]:
    """Return an ordered, case-insensitive, de-duplicated list of hashtags in text."""
    seen: dict[str, None] = {}
    for tag in HASHTAG_RE.findall(text or ""):
        seen.setdefault(tag.lower(), None)
    return list(seen)


def extract_metadata(info: dict) -> dict:
    """Pull the fields the skill needs from a yt-dlp info-json dict."""
    description = info.get("description") or ""
    return {
        "video_id": info.get("id"),
        "url": info.get("webpage_url"),
        "author_handle": info.get("uploader_id") or info.get("uploader"),
        "author_name": info.get("creator") or info.get("uploader"),
        "description": description,
        "hashtags": extract_hashtags(description),
        "duration_seconds": info.get("duration"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "comment_count": info.get("comment_count"),
        "repost_count": info.get("repost_count"),
        "music": info.get("track") or info.get("music") or None,
        "upload_date": info.get("upload_date"),
    }


# --- Frame selection ---------------------------------------------------------
def needs_even_sampling(scene_frame_count: int) -> bool:
    """True if scene detection produced too few frames to rely on."""
    return scene_frame_count < MIN_SCENE_FRAMES


def evenly_spaced_indices(total: int, max_count: int) -> list[int]:
    """Pick up to max_count indices spread evenly across range(total)."""
    if max_count <= 0 or total <= 0:
        return []
    if total <= max_count:
        return list(range(total))
    step = total / max_count
    return [min(total - 1, int(i * step)) for i in range(max_count)]


# --- Output bundle -----------------------------------------------------------
def make_output_dir(base: Path, video_id: str, now: datetime | None = None) -> Path:
    """Create and return base/<UTC-timestamp>-<video-id>/."""
    moment = now or datetime.now(timezone.utc)
    stamp = moment.strftime("%Y%m%d-%H%M%S")
    out = base / f"{stamp}-{video_id}"
    out.mkdir(parents=True, exist_ok=True)
    return out


def build_manifest(
    run_type: str,
    output_dir: Path,
    frame_paths: list[Path],
    transcript_text: str,
    metadata: dict,
) -> dict:
    """Assemble the manifest dict the skill consumes to write the summary."""
    return {
        "type": run_type,
        "output_dir": str(output_dir),
        "frames": [str(p) for p in frame_paths],
        "frame_count": len(frame_paths),
        "transcript": transcript_text,
        "has_speech": bool(transcript_text.strip()),
        "metadata": metadata,
    }


# --- External processes ------------------------------------------------------
def check_prereqs() -> list[str]:
    """Return the required CLI tools that are missing from PATH, in REQUIRED_TOOLS order."""
    return [tool for tool in REQUIRED_TOOLS if shutil.which(tool) is None]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a command; raise RuntimeError with stderr on non-zero exit."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"`{' '.join(cmd[:2])} ...` failed: {result.stderr.strip() or 'unknown error'}"
        )
    return result


def download(url: str, dl_dir: Path) -> dict:
    """Download the post into dl_dir with yt-dlp; return the first info-json dict."""
    if dl_dir.exists():
        shutil.rmtree(dl_dir)
    dl_dir.mkdir(parents=True, exist_ok=True)
    template = str(dl_dir / "%(autonumber)03d.%(ext)s")
    # Prefer h264: TikTok's HEVC (bytevc1) variants are often delivered
    # video-only despite advertising an audio codec, which breaks transcription.
    run(["yt-dlp", "-S", "vcodec:h264", "--write-info-json", "-o", template, url])
    info_files = sorted(dl_dir.glob("*.info.json"))
    if not info_files:
        raise RuntimeError(
            "yt-dlp produced no metadata — the post may be private, deleted, or region-locked."
        )
    return json.loads(info_files[0].read_text(encoding="utf-8"))


def _renumber_frames(raw_frames: list[Path], frames_dir: Path) -> list[Path]:
    """Rename kept raw frames to frame-NN.jpg; delete any leftover raw frames."""
    final: list[Path] = []
    for idx, src in enumerate(raw_frames, start=1):
        dst = frames_dir / f"frame-{idx:02d}.jpg"
        src.replace(dst)
        final.append(dst)
    for leftover in frames_dir.glob("raw-*.jpg"):
        leftover.unlink()
    return final


def extract_frames(video: Path, frames_dir: Path, max_frames: int, duration: float) -> list[Path]:
    """Extract up to max_frames keyframes: scene detection, then even-sampling fallback."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    scale = f"scale=-2:'min({FRAME_LONG_EDGE},ih)'"
    run([
        "ffmpeg", "-y", "-i", str(video),
        "-vf", f"select='gt(scene,{SCENE_THRESHOLD})',{scale}",
        "-vsync", "vfr", str(frames_dir / "raw-%03d.jpg"),
    ])
    raw = sorted(frames_dir.glob("raw-*.jpg"))
    if needs_even_sampling(len(raw)):
        for frame in raw:
            frame.unlink()
        fps = max(0.1, max_frames / max(duration, 1.0))
        run([
            "ffmpeg", "-y", "-i", str(video),
            "-vf", f"fps={fps:.4f},{scale}",
            str(frames_dir / "raw-%03d.jpg"),
        ])
        raw = sorted(frames_dir.glob("raw-*.jpg"))
    kept = [raw[i] for i in evenly_spaced_indices(len(raw), max_frames)]
    return _renumber_frames(kept, frames_dir)


def collect_photo_frames(dl_dir: Path, frames_dir: Path, max_frames: int) -> list[Path]:
    """Copy carousel images from dl_dir into frames_dir as frame-NN.<ext>."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    images = sorted(p for p in dl_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    kept = [images[i] for i in evenly_spaced_indices(len(images), max_frames)]
    final: list[Path] = []
    for idx, src in enumerate(kept, start=1):
        dst = frames_dir / f"frame-{idx:02d}{src.suffix.lower()}"
        shutil.copy2(src, dst)
        final.append(dst)
    return final


def extract_audio(video: Path, audio_path: Path) -> None:
    """Extract 16 kHz mono WAV audio from the video."""
    run(["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio_path)])


def transcribe(audio_path: Path, out_dir: Path, model: str) -> str:
    """Transcribe audio with local whisper; write transcript.txt/json, return the text."""
    run([
        "whisper", str(audio_path),
        "--model", model,
        "--output_format", "all",
        "--output_dir", str(out_dir),
        "--condition_on_previous_text", "False",
        "--verbose", "False",
    ])
    stem = audio_path.stem
    text = ""
    for fmt in ("txt", "json", "srt", "vtt", "tsv"):
        produced = out_dir / f"{stem}.{fmt}"
        if not produced.exists():
            continue
        if fmt == "txt":
            text = produced.read_text(encoding="utf-8").strip()
            produced.replace(out_dir / "transcript.txt")
        elif fmt == "json":
            produced.replace(out_dir / "transcript.json")
        else:
            produced.unlink()
    return text


# --- Orchestration -----------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    """Download a TikTok post, build the artifact bundle, print the output dir."""
    parser = argparse.ArgumentParser(description="Download and analyze a TikTok post.")
    parser.add_argument("url", help="TikTok video or photo URL")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "output",
                        help="base output directory (default: output/ next to this script)")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES,
                        help=f"maximum keyframes to keep (default: {DEFAULT_MAX_FRAMES})")
    parser.add_argument("--whisper-model", default=DEFAULT_WHISPER_MODEL,
                        help=f"whisper model name (default: {DEFAULT_WHISPER_MODEL})")
    args = parser.parse_args(argv)

    missing = check_prereqs()
    if missing:
        print(f"ERROR: missing required tools: {', '.join(missing)}", file=sys.stderr)
        return 2
    try:
        url = validate_url(args.url)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    work = args.out / "_work"
    dl_dir = work / "dl"
    try:
        info = download(url, dl_dir)
    except RuntimeError as exc:
        print(f"ERROR: download failed: {exc}", file=sys.stderr)
        shutil.rmtree(work, ignore_errors=True)
        return 1

    metadata = extract_metadata(info)
    video_id = metadata["video_id"] or "unknown"
    out_dir = make_output_dir(args.out, video_id)
    frames_dir = out_dir / "frames"
    transcript_text = ""

    videos = sorted(dl_dir.glob("*.mp4"))
    try:
        if videos:
            run_type = "video"
            video_path = out_dir / "video.mp4"
            videos[0].replace(video_path)
            duration = float(metadata["duration_seconds"] or 0) or 1.0
            frame_paths = extract_frames(video_path, frames_dir, args.max_frames, duration)
            try:
                audio_path = out_dir / "audio.wav"
                extract_audio(video_path, audio_path)
                transcript_text = transcribe(audio_path, out_dir, args.whisper_model)
            except RuntimeError as exc:
                print(f"WARNING: audio/transcription skipped: {exc}", file=sys.stderr)
        else:
            run_type = "photo"
            frame_paths = collect_photo_frames(dl_dir, frames_dir, args.max_frames)
            if not frame_paths:
                print("ERROR: download contained neither a video nor images.", file=sys.stderr)
                shutil.rmtree(work, ignore_errors=True)
                return 1

        (out_dir / "info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
        manifest = build_manifest(run_type, out_dir, frame_paths, transcript_text, metadata)
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    except RuntimeError as exc:
        print(f"ERROR: processing failed: {exc}", file=sys.stderr)
        shutil.rmtree(work, ignore_errors=True)
        return 1
    shutil.rmtree(work, ignore_errors=True)

    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
