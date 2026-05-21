from datetime import datetime, timezone

from social_media_watcher import manifest


def test_extract_hashtags_dedupes_case_insensitively():
    assert manifest.extract_hashtags("a #AI #ai b #ML") == ["ai", "ml"]
    assert manifest.extract_hashtags("") == []


def test_make_output_dir(tmp_path):
    moment = datetime(2026, 5, 21, 9, 8, 7, tzinfo=timezone.utc)
    out = manifest.make_output_dir(tmp_path, "youtube", "vid9", now=moment)
    assert out == tmp_path / "20260521-090807-youtube-vid9"
    assert out.is_dir()


def test_is_long_form_threshold():
    assert manifest.is_long_form(599, 600) is False
    assert manifest.is_long_form(600, 600) is True
    assert manifest.is_long_form(None, 600) is False


def test_extract_metadata_pulls_fields_and_chapters():
    info = {
        "id": "v1", "webpage_url": "https://yt/v1", "uploader_id": "chan",
        "creator": "Chan", "description": "deep dive #ai", "duration": 1800,
        "view_count": 5, "like_count": 4, "comment_count": 3, "repost_count": 2,
        "track": None, "upload_date": "20260520",
        "chapters": [
            {"start_time": 0, "end_time": 60, "title": "Intro"},
            {"start_time": 60, "end_time": 1800, "title": "Main"},
        ],
    }
    meta = manifest.extract_metadata(info, platform="youtube")
    assert meta["platform"] == "youtube"
    assert meta["video_id"] == "v1"
    assert meta["duration_seconds"] == 1800
    assert meta["hashtags"] == ["ai"]
    assert len(meta["chapters"]) == 2
    assert meta["chapters"][0] == {"start": 0, "end": 60, "title": "Intro"}


def test_extract_metadata_tolerates_missing_chapters():
    meta = manifest.extract_metadata({"id": "x"}, platform="generic")
    assert meta["chapters"] == []
    assert meta["duration_seconds"] is None


def test_build_manifest_long_form_with_chapters(tmp_path):
    frames = [tmp_path / "frame-01.jpg", tmp_path / "frame-02.jpg"]
    m = manifest.build_manifest(
        run_type="video", form="long", platform="youtube", output_dir=tmp_path,
        frame_paths=frames, transcript_text="hello", transcript_source="captions",
        chapters=[{"start": 0, "end": 60, "title": "Intro", "frame": "frame-01.jpg"}],
        metadata={"video_id": "v1"},
    )
    assert m["type"] == "video"
    assert m["form"] == "long"
    assert m["platform"] == "youtube"
    assert m["transcript_source"] == "captions"
    assert m["has_speech"] is True
    assert m["frame_count"] == 2
    assert m["chapters"][0]["frame"] == "frame-01.jpg"


def test_build_manifest_short_form_no_speech(tmp_path):
    m = manifest.build_manifest(
        run_type="video", form="short", platform="tiktok", output_dir=tmp_path,
        frame_paths=[tmp_path / "frame-01.jpg"], transcript_text="  ",
        transcript_source="none", chapters=[], metadata={},
    )
    assert m["form"] == "short"
    assert m["has_speech"] is False
    assert m["chapters"] == []
