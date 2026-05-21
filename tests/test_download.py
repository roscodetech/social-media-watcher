from social_media_watcher import download
from social_media_watcher.platforms import resolve


def test_check_prereqs_all_present(monkeypatch):
    monkeypatch.setattr(download.shutil, "which", lambda _n: "/usr/bin/x")
    assert download.check_prereqs() == []


def test_check_prereqs_reports_missing(monkeypatch):
    monkeypatch.setattr(
        download.shutil, "which",
        lambda n: None if n in ("ffmpeg", "whisper") else "/x",
    )
    assert download.check_prereqs() == ["ffmpeg", "whisper"]


def test_build_ytdlp_cmd_includes_adapter_args_and_subs(tmp_path):
    adapter = resolve("https://www.tiktok.com/@u/video/1")
    cmd = download.build_ytdlp_cmd(
        "https://www.tiktok.com/@u/video/1", tmp_path, adapter, cookies_from_browser=None
    )
    assert cmd[0] == "yt-dlp"
    assert "-S" in cmd and "vcodec:h264" in cmd
    assert "--write-info-json" in cmd
    assert "--write-subs" in cmd and "--write-auto-subs" in cmd
    assert "--sub-langs" in cmd
    assert "--convert-subs" in cmd
    assert cmd[cmd.index("--convert-subs") + 1] == "srt"
    assert "--cookies-from-browser" not in cmd


def test_build_ytdlp_cmd_adds_cookies_when_requested(tmp_path):
    adapter = resolve("https://example.com/x")
    cmd = download.build_ytdlp_cmd(
        "https://example.com/x", tmp_path, adapter, cookies_from_browser="chrome"
    )
    assert "--cookies-from-browser" in cmd
    assert cmd[cmd.index("--cookies-from-browser") + 1] == "chrome"
