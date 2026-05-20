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
