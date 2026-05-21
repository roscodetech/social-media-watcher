from social_media_watcher import transcribe

SRT = """1
00:00:00,000 --> 00:00:02,500
Hello and welcome.

2
00:00:02,500 --> 00:00:05,000
Today we cover three things.
"""


def test_parse_srt_returns_segments(tmp_path):
    srt = tmp_path / "001.en.srt"
    srt.write_text(SRT, encoding="utf-8")
    segs = transcribe.parse_srt(srt)
    assert len(segs) == 2
    assert segs[0]["start"] == 0.0
    assert segs[0]["text"] == "Hello and welcome."
    assert segs[1]["start"] == 2.5


def test_parse_srt_empty_file(tmp_path):
    srt = tmp_path / "empty.srt"
    srt.write_text("", encoding="utf-8")
    assert transcribe.parse_srt(srt) == []


def test_segments_to_text_joins_with_spaces():
    segs = [{"start": 0.0, "text": "Hello."}, {"start": 2.5, "text": "World."}]
    assert transcribe.segments_to_text(segs) == "Hello. World."


def test_find_caption_file_prefers_srt(tmp_path):
    (tmp_path / "001.info.json").write_text("{}", encoding="utf-8")
    (tmp_path / "001.en.srt").write_text(SRT, encoding="utf-8")
    found = transcribe.find_caption_file(tmp_path)
    assert found is not None and found.suffix == ".srt"


def test_find_caption_file_none_when_absent(tmp_path):
    (tmp_path / "001.info.json").write_text("{}", encoding="utf-8")
    assert transcribe.find_caption_file(tmp_path) is None
