import tiktok_watch


def test_extract_hashtags_finds_and_dedupes():
    text = "Loving this #Recipe #recipe #QuickMeal cooking content #quickmeal"
    assert tiktok_watch.extract_hashtags(text) == ["recipe", "quickmeal"]


def test_extract_hashtags_empty_text():
    assert tiktok_watch.extract_hashtags("") == []
    assert tiktok_watch.extract_hashtags(None) == []


def test_extract_metadata_pulls_expected_fields():
    info = {
        "id": "7234567890123456789",
        "webpage_url": "https://www.tiktok.com/@chef/video/7234567890123456789",
        "uploader_id": "chef",
        "uploader": "chef",
        "creator": "The Chef",
        "description": "3-ingredient pasta #pasta #easyrecipe",
        "duration": 32,
        "view_count": 100000,
        "like_count": 8000,
        "comment_count": 120,
        "repost_count": 50,
        "track": "Original Sound",
        "upload_date": "20260518",
    }
    meta = tiktok_watch.extract_metadata(info)
    assert meta["video_id"] == "7234567890123456789"
    assert meta["author_handle"] == "chef"
    assert meta["author_name"] == "The Chef"
    assert meta["description"] == "3-ingredient pasta #pasta #easyrecipe"
    assert meta["hashtags"] == ["pasta", "easyrecipe"]
    assert meta["duration_seconds"] == 32
    assert meta["like_count"] == 8000
    assert meta["music"] == "Original Sound"
    assert meta["upload_date"] == "20260518"


def test_extract_metadata_tolerates_missing_fields():
    meta = tiktok_watch.extract_metadata({"id": "123"})
    assert meta["video_id"] == "123"
    assert meta["description"] == ""
    assert meta["hashtags"] == []
    assert meta["duration_seconds"] is None
    assert meta["music"] is None
