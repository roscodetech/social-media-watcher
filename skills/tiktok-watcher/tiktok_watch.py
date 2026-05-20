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
