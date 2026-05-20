from datetime import datetime, timezone
from pathlib import Path

import tiktok_watch


def test_make_output_dir_uses_timestamp_and_id(tmp_path):
    moment = datetime(2026, 5, 20, 14, 30, 5, tzinfo=timezone.utc)
    out = tiktok_watch.make_output_dir(tmp_path, "7234567890", now=moment)
    assert out == tmp_path / "20260520-143005-7234567890"
    assert out.is_dir()


def test_build_manifest_video_with_speech(tmp_path):
    frames = [tmp_path / "frame-01.jpg", tmp_path / "frame-02.jpg"]
    manifest = tiktok_watch.build_manifest(
        run_type="video",
        output_dir=tmp_path,
        frame_paths=frames,
        transcript_text="Here is how you make pasta.",
        metadata={"video_id": "123", "hashtags": ["pasta"]},
    )
    assert manifest["type"] == "video"
    assert manifest["output_dir"] == str(tmp_path)
    assert manifest["frames"] == [str(frames[0]), str(frames[1])]
    assert manifest["frame_count"] == 2
    assert manifest["transcript"] == "Here is how you make pasta."
    assert manifest["has_speech"] is True
    assert manifest["metadata"]["video_id"] == "123"


def test_build_manifest_marks_no_speech_for_empty_transcript(tmp_path):
    manifest = tiktok_watch.build_manifest(
        run_type="video",
        output_dir=tmp_path,
        frame_paths=[tmp_path / "frame-01.jpg"],
        transcript_text="   ",
        metadata={},
    )
    assert manifest["has_speech"] is False
