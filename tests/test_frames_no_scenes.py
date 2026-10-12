"""Regression: a video with no scene changes made ffmpeg write zero frames and exit non-zero,
which raised before the even-sampling fallback could run (seen on real Instagram reels)."""

import shutil
import subprocess

import pytest

from social_media_watcher import frames

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not on PATH")


@pytest.fixture
def static_video(tmp_path):
    video = tmp_path / "static.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=teal:s=320x568:d=6:r=25",
         "-pix_fmt", "yuv420p", str(video)],
        check=True,
    )
    return video


def test_static_video_falls_back_to_even_sampling(static_video, tmp_path):
    out = frames.extract_frames_scene(static_video, tmp_path / "frames", max_frames=6, duration=6.0)
    assert len(out) >= frames.MIN_SCENE_FRAMES
    assert all(p.name.startswith("frame-") and p.exists() for p in out)


def test_other_scene_pass_errors_still_raise(tmp_path):
    with pytest.raises(RuntimeError):
        frames.extract_frames_scene(tmp_path / "missing.mp4", tmp_path / "frames", max_frames=6, duration=6.0)
