import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "tiktok-watcher"
SCRIPT = SKILL_DIR / "tiktok_watch.py"


@pytest.mark.integration
def test_end_to_end_produces_artifact_bundle(tmp_path):
    """Run the extractor against a real public TikTok URL and check the bundle.

    Set TIKTOK_TEST_URL to a public TikTok video URL to run this test:
        TIKTOK_TEST_URL=https://www.tiktok.com/@user/video/123 pytest -m integration
    """
    url = os.environ.get("TIKTOK_TEST_URL")
    if not url:
        pytest.skip("set TIKTOK_TEST_URL to run the end-to-end test")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), url,
         "--out", str(tmp_path), "--whisper-model", "tiny"],
        capture_output=True, text=True, timeout=900,
    )
    assert result.returncode == 0, result.stderr

    lines = [line for line in result.stdout.strip().splitlines() if line]
    assert len(lines) == 1, f"expected one stdout line (the output dir), got:\n{result.stdout}"
    out_dir = Path(lines[-1])
    assert out_dir.is_dir(), f"output dir not found; stdout was:\n{result.stdout}"

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["type"] in ("video", "photo")
    assert manifest["frame_count"] > 0
    assert len(manifest["frames"]) == manifest["frame_count"]
    for frame in manifest["frames"]:
        assert Path(frame).is_absolute(), f"expected absolute frame path, got {frame!r}"
        assert Path(frame).is_file()
    assert (out_dir / "info.json").is_file()
    assert manifest["metadata"]["video_id"]
