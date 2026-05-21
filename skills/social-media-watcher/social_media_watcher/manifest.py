"""Output-directory naming, yt-dlp metadata extraction, and manifest assembly."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

_HASHTAG_RE = re.compile(r"#(\w+)")


def extract_hashtags(text: str) -> list[str]:
    """Ordered, case-insensitive, de-duplicated hashtags found in text."""
    seen: dict[str, None] = {}
    for tag in _HASHTAG_RE.findall(text or ""):
        seen.setdefault(tag.lower(), None)
    return list(seen)


def make_output_dir(
    base: Path, platform: str, video_id: str, now: datetime | None = None
) -> Path:
    """Create and return base/<UTC-timestamp>-<platform>-<video-id>/."""
    moment = now or datetime.now(timezone.utc)
    stamp = moment.strftime("%Y%m%d-%H%M%S")
    out = base / f"{stamp}-{platform}-{video_id}"
    out.mkdir(parents=True, exist_ok=True)
    return out


def is_long_form(duration_seconds: float | None, threshold: int) -> bool:
    """True when a known duration meets or exceeds the long-form threshold."""
    return duration_seconds is not None and duration_seconds >= threshold


def _extract_chapters(info: dict) -> list[dict]:
    """Normalize yt-dlp's chapters list to [{start, end, title}, ...]."""
    chapters: list[dict] = []
    for ch in info.get("chapters") or []:
        chapters.append({
            "start": ch.get("start_time"),
            "end": ch.get("end_time"),
            "title": ch.get("title") or "",
        })
    return chapters


def extract_metadata(info: dict, platform: str) -> dict:
    """Pull the fields the skill needs from a yt-dlp info-json dict."""
    description = info.get("description") or ""
    return {
        "platform": platform,
        "video_id": info.get("id"),
        "url": info.get("webpage_url"),
        "title": info.get("title"),
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
        "chapters": _extract_chapters(info),
    }


def build_manifest(
    run_type: str,
    form: str,
    platform: str,
    output_dir: Path,
    frame_paths: list[Path],
    transcript_text: str,
    transcript_source: str,
    chapters: list[dict],
    metadata: dict,
) -> dict:
    """Assemble the manifest dict the skill consumes to write the summary."""
    return {
        "type": run_type,
        "form": form,
        "platform": platform,
        "output_dir": str(output_dir),
        "frames": [str(p) for p in frame_paths],
        "frame_count": len(frame_paths),
        "transcript": transcript_text,
        "transcript_source": transcript_source,
        "has_speech": bool(transcript_text.strip()),
        "chapters": chapters,
        "metadata": metadata,
    }
