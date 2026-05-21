import pytest

from social_media_watcher import platforms


@pytest.mark.parametrize("url,expected", [
    ("https://www.tiktok.com/@u/video/123", "tiktok"),
    ("https://vm.tiktok.com/ZSabc/", "tiktok"),
    ("https://www.youtube.com/watch?v=abc", "youtube"),
    ("https://youtu.be/abc", "youtube"),
    ("https://www.instagram.com/reel/abc/", "instagram"),
    ("https://x.com/u/status/123", "twitter"),
    ("https://twitter.com/u/status/123", "twitter"),
    ("https://www.reddit.com/r/v/comments/abc/x/", "reddit"),
    ("https://www.twitch.tv/videos/123", "twitch"),
    ("https://vimeo.com/123", "vimeo"),
    ("https://example.com/video/123", "generic"),
])
def test_resolve_picks_the_right_adapter(url, expected):
    assert platforms.resolve(url).name == expected


def test_validate_url_returns_url_and_adapter():
    url, adapter = platforms.validate_url("  https://www.tiktok.com/@u/video/123  ")
    assert url == "https://www.tiktok.com/@u/video/123"
    assert adapter.name == "tiktok"


def test_validate_url_rejects_non_url():
    with pytest.raises(ValueError, match="valid URL"):
        platforms.validate_url("not a url")


def test_validate_url_rejects_tiktok_profile():
    with pytest.raises(ValueError, match="single tiktok post"):
        platforms.validate_url("https://www.tiktok.com/@creator")


def test_validate_url_rejects_youtube_channel():
    with pytest.raises(ValueError, match="single youtube post"):
        platforms.validate_url("https://www.youtube.com/@creator")


def test_validate_url_accepts_youtube_shorts_and_watch():
    assert platforms.validate_url("https://youtube.com/shorts/abc")[1].name == "youtube"
    assert platforms.validate_url("https://youtu.be/abc")[1].name == "youtube"


def test_validate_url_generic_accepts_any_http_url():
    url, adapter = platforms.validate_url("https://example.com/clip/9")
    assert adapter.name == "generic"


def test_tiktok_adapter_carries_h264_format_args():
    assert platforms.resolve("https://www.tiktok.com/@u/video/1").ytdlp_format_args == ("-S", "vcodec:h264")
