import tiktok_watch


def test_check_prereqs_empty_when_all_present(monkeypatch):
    monkeypatch.setattr(tiktok_watch.shutil, "which", lambda _name: "/usr/bin/tool")
    assert tiktok_watch.check_prereqs() == []


def test_check_prereqs_reports_missing_tools(monkeypatch):
    def fake_which(name):
        return None if name in ("whisper", "ffmpeg") else "/usr/bin/tool"

    monkeypatch.setattr(tiktok_watch.shutil, "which", fake_which)
    assert tiktok_watch.check_prereqs() == ["ffmpeg", "whisper"]
