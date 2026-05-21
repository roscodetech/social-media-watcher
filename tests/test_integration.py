import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "social-media-watcher"


def _run(url: str, out: Path) -> Path:
    result = subprocess.run(
        [sys.executable, "-m", "social_media_watcher", url,
         "--out", str(out), "--whisper-model", "tiny"],
        capture_output=True, text=True, timeout=1800, cwd=str(SKILL_DIR),
    )
    assert result.returncode == 0, result.stderr
    lines = [ln for ln in result.stdout.strip().splitlines() if ln]
    assert len(lines) == 1, f"expected one stdout line, got:\n{result.stdout}"
    out_dir = Path(lines[-1])
    assert out_dir.is_dir(), f"output dir missing; stdout:\n{result.stdout}"
    return out_dir


@pytest.mark.integration
def test_short_form_tiktok(tmp_path):
    """Set SMW_TEST_SHORT_URL to a public short-form video URL."""
    url = os.environ.get("SMW_TEST_SHORT_URL")
    if not url:
        pytest.skip("set SMW_TEST_SHORT_URL to run the short-form e2e test")
    out_dir = _run(url, tmp_path)
    m = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert m["type"] in ("video", "photo")
    assert m["form"] == "short"
    assert m["frame_count"] > 0
    for frame in m["frames"]:
        assert Path(frame).is_absolute() and Path(frame).is_file()
    assert m["metadata"]["video_id"]


@pytest.mark.integration
def test_long_form_youtube(tmp_path):
    """Set SMW_TEST_LONG_URL to a public long-form (>=10 min) YouTube URL."""
    url = os.environ.get("SMW_TEST_LONG_URL")
    if not url:
        pytest.skip("set SMW_TEST_LONG_URL to run the long-form e2e test")
    out_dir = _run(url, tmp_path)
    m = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert m["form"] == "long"
    assert m["platform"] == "youtube"
    assert m["frame_count"] > 0
    assert m["transcript_source"] in ("captions", "whisper", "none")
