"""CLI entry point — orchestrates download, frames, transcript, manifest."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from social_media_watcher import (
    DEFAULT_LONG_FORM_SECONDS,
    DEFAULT_MAX_FRAMES,
    DEFAULT_WHISPER_MODEL,
    LONG_FORM_MAX_FRAMES,
)
from social_media_watcher import frames as frames_mod
from social_media_watcher import manifest as manifest_mod
from social_media_watcher.download import check_prereqs, download
from social_media_watcher.platforms import validate_url
from social_media_watcher.transcribe import resolve_transcript


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="social_media_watcher",
        description="Download and analyze a social-media video post.",
    )
    parser.add_argument("url", help="video URL from any supported platform")
    parser.add_argument("--out", type=Path,
                        default=Path(__file__).resolve().parent.parent / "output",
                        help="base output directory")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES,
                        help=f"keyframes for short-form video (default: {DEFAULT_MAX_FRAMES})")
    parser.add_argument("--whisper-model", default=DEFAULT_WHISPER_MODEL,
                        help=f"whisper model (default: {DEFAULT_WHISPER_MODEL})")
    parser.add_argument("--cookies-from-browser", default=None,
                        help="browser to read cookies from (e.g. chrome, firefox)")
    parser.add_argument("--long-form-threshold", type=int,
                        default=DEFAULT_LONG_FORM_SECONDS,
                        help=f"seconds at which a video counts as long-form "
                             f"(default: {DEFAULT_LONG_FORM_SECONDS})")
    return parser.parse_args(argv)


def _chapters_with_frames(chapters: list[dict], seconds: list[float],
                          frame_paths: list[Path]) -> list[dict]:
    """Attach the nearest extracted frame filename to each chapter."""
    enriched: list[dict] = []
    for ch in chapters:
        start = ch.get("start") or 0.0
        idx = min(range(len(seconds)), key=lambda i: abs(seconds[i] - start)) \
            if seconds else 0
        frame = frame_paths[idx].name if 0 <= idx < len(frame_paths) else None
        enriched.append({**ch, "frame": frame})
    return enriched


def main(argv: list[str] | None = None) -> int:
    """Download a post, build the artifact bundle, print the output dir."""
    args = _parse_args(argv)

    missing = check_prereqs()
    if missing:
        print(f"ERROR: missing required tools: {', '.join(missing)}", file=sys.stderr)
        return 2
    try:
        url, adapter = validate_url(args.url)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    work = args.out / "_work"
    dl_dir = work / "dl"
    try:
        info = download(url, dl_dir, adapter, args.cookies_from_browser)
    except RuntimeError as exc:
        print(f"ERROR: download failed: {exc}", file=sys.stderr)
        shutil.rmtree(work, ignore_errors=True)
        return 1

    metadata = manifest_mod.extract_metadata(info, adapter.name)
    video_id = metadata["video_id"] or "unknown"
    duration = float(metadata["duration_seconds"] or 0)
    long_form = manifest_mod.is_long_form(
        metadata["duration_seconds"], args.long_form_threshold)
    form = "long" if long_form else "short"
    out_dir = manifest_mod.make_output_dir(args.out, adapter.name, video_id)
    frames_dir = out_dir / "frames"
    chapters = metadata["chapters"]

    try:
        videos = sorted(dl_dir.glob("*.mp4"))
        if videos:
            run_type = "video"
            video_path = out_dir / "video.mp4"
            videos[0].replace(video_path)
            if long_form:
                if chapters:
                    seconds = frames_mod.chapter_frame_seconds(
                        chapters, max(duration, 1.0), LONG_FORM_MAX_FRAMES)
                else:
                    seconds = frames_mod.even_frame_seconds(
                        max(duration, 1.0), LONG_FORM_MAX_FRAMES)
                frame_paths = frames_mod.extract_frames_at(
                    video_path, frames_dir, seconds)
                chapters = _chapters_with_frames(chapters, seconds, frame_paths)
            else:
                seconds = []
                frame_paths = frames_mod.extract_frames_scene(
                    video_path, frames_dir, args.max_frames, max(duration, 1.0))
            transcript_text, transcript_source = resolve_transcript(
                dl_dir, video_path, out_dir, args.whisper_model)
        else:
            run_type = "photo"
            frame_paths = frames_mod.collect_photo_frames(
                dl_dir, frames_dir, args.max_frames)
            if not frame_paths:
                print("ERROR: download contained neither a video nor images.",
                      file=sys.stderr)
                shutil.rmtree(work, ignore_errors=True)
                return 1
            transcript_text, transcript_source = resolve_transcript(
                dl_dir, None, out_dir, args.whisper_model)

        (out_dir / "info.json").write_text(
            json.dumps(info, indent=2), encoding="utf-8")
        manifest = manifest_mod.build_manifest(
            run_type=run_type, form=form, platform=adapter.name,
            output_dir=out_dir, frame_paths=frame_paths,
            transcript_text=transcript_text, transcript_source=transcript_source,
            chapters=chapters, metadata=metadata)
        (out_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8")
    except RuntimeError as exc:
        print(f"ERROR: processing failed: {exc}", file=sys.stderr)
        shutil.rmtree(work, ignore_errors=True)
        return 1

    shutil.rmtree(work, ignore_errors=True)
    print(str(out_dir))
    return 0
