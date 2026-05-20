import pytest

import tiktok_watch


@pytest.mark.parametrize("url", [
    "https://www.tiktok.com/@creator/video/7234567890123456789",
    "https://tiktok.com/@creator/video/7234567890123456789",
    "https://m.tiktok.com/v/7234567890123456789.html",
    "https://vm.tiktok.com/ZMabc123/",
    "https://vt.tiktok.com/ZSabc123/",
    "  https://www.tiktok.com/t/ZTabc123/  ",
])
def test_is_tiktok_url_accepts_tiktok_hosts(url):
    assert tiktok_watch.is_tiktok_url(url) is True


@pytest.mark.parametrize("url", [
    "https://example.com/@creator/video/123",
    "https://youtube.com/watch?v=abc",
    "ftp://tiktok.com/@creator/video/123",
    "not a url at all",
    "",
])
def test_is_tiktok_url_rejects_non_tiktok(url):
    assert tiktok_watch.is_tiktok_url(url) is False


def test_extract_video_id_from_full_url():
    url = "https://www.tiktok.com/@creator/video/7234567890123456789"
    assert tiktok_watch.extract_video_id(url) == "7234567890123456789"


def test_extract_video_id_returns_none_for_short_link():
    assert tiktok_watch.extract_video_id("https://vm.tiktok.com/ZMabc123/") is None


@pytest.mark.parametrize("url", [
    "https://www.tiktok.com/@creator/video/7234567890123456789",
    "https://www.tiktok.com/@creator/photo/7234567890123456789",
    "https://www.tiktok.com/t/ZTabc123/",
    "https://vm.tiktok.com/ZMabc123/",
])
def test_looks_like_single_post_accepts_posts(url):
    assert tiktok_watch.looks_like_single_post(url) is True


@pytest.mark.parametrize("url", [
    "https://www.tiktok.com/@creator",
    "https://www.tiktok.com/foryou",
    "https://www.tiktok.com/",
])
def test_looks_like_single_post_rejects_profiles_and_feeds(url):
    assert tiktok_watch.looks_like_single_post(url) is False


def test_validate_url_returns_trimmed_url():
    raw = "  https://www.tiktok.com/@creator/video/7234567890123456789  "
    assert tiktok_watch.validate_url(raw) == raw.strip()


def test_validate_url_rejects_non_tiktok():
    with pytest.raises(ValueError, match="Not a TikTok URL"):
        tiktok_watch.validate_url("https://youtube.com/watch?v=abc")


def test_validate_url_rejects_profile_url():
    with pytest.raises(ValueError, match="single TikTok post"):
        tiktok_watch.validate_url("https://www.tiktok.com/@creator")
