"""Prerequisite checks, a subprocess helper, and the yt-dlp download step."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from social_media_watcher import REQUIRED_TOOLS
from social_media_watcher.platforms import PlatformAdapter


def check_prereqs() -> list[str]:
    """Return the required CLI tools missing from PATH, in REQUIRED_TOOLS order."""
    return [tool for tool in REQUIRED_TOOLS if shutil.which(tool) is None]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a command; raise RuntimeError with stderr on non-zero exit."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"`{' '.join(cmd[:2])} ...` failed: {result.stderr.strip() or 'unknown error'}"
        )
    return result


def build_ytdlp_cmd(
    url: str,
    dl_dir: Path,
    adapter: PlatformAdapter,
    cookies_from_browser: str | None,
) -> list[str]:
    """Assemble the yt-dlp argv: metadata, captions, adapter quirks, optional cookies."""
    cmd = [
        "yt-dlp",
        "--write-info-json",
        "--write-subs", "--write-auto-subs",
        "--sub-langs", "en.*,en",
        "--convert-subs", "srt",
        *adapter.ytdlp_format_args,
        "-o", str(dl_dir / "%(autonumber)03d.%(ext)s"),
    ]
    if cookies_from_browser:
        cmd += ["--cookies-from-browser", cookies_from_browser]
    cmd.append(url)
    return cmd


def download(
    url: str,
    dl_dir: Path,
    adapter: PlatformAdapter,
    cookies_from_browser: str | None = None,
) -> dict:
    """Download the post into dl_dir with yt-dlp; return the first info-json dict."""
    if dl_dir.exists():
        shutil.rmtree(dl_dir)
    dl_dir.mkdir(parents=True, exist_ok=True)
    run(build_ytdlp_cmd(url, dl_dir, adapter, cookies_from_browser))
    info_files = sorted(dl_dir.glob("*.info.json"))
    if not info_files:
        raise RuntimeError(
            "yt-dlp produced no metadata — the post may be private, deleted, or "
            "region-locked. For private content, retry with --cookies-from-browser."
        )
    return json.loads(info_files[0].read_text(encoding="utf-8"))
