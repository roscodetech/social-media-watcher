from social_media_watcher import frames


def test_needs_even_sampling():
    assert frames.needs_even_sampling(3) is True
    assert frames.needs_even_sampling(4) is False


def test_evenly_spaced_indices():
    assert frames.evenly_spaced_indices(5, 14) == [0, 1, 2, 3, 4]
    assert frames.evenly_spaced_indices(5, 5) == [0, 1, 2, 3, 4]
    result = frames.evenly_spaced_indices(100, 10)
    assert len(result) == 10 and result == sorted(result) and max(result) <= 99
    assert frames.evenly_spaced_indices(0, 14) == []
    assert frames.evenly_spaced_indices(10, 0) == []


def test_chapter_frame_seconds_includes_all_chapter_starts():
    chapters = [{"start": 0}, {"start": 120}, {"start": 300}]
    secs = frames.chapter_frame_seconds(chapters, duration=600.0, max_frames=30)
    assert 0.0 in secs and 120.0 in secs and 300.0 in secs
    assert len(secs) <= 30
    assert all(0 <= s < 600 for s in secs)
    assert secs == sorted(secs)


def test_chapter_frame_seconds_downselects_when_many_chapters():
    chapters = [{"start": float(i * 10)} for i in range(50)]
    secs = frames.chapter_frame_seconds(chapters, duration=600.0, max_frames=12)
    assert len(secs) == 12
    assert secs == sorted(secs)
    assert all(s in {c["start"] for c in chapters} for s in secs)


def test_even_frame_seconds_spreads_across_duration():
    secs = frames.even_frame_seconds(duration=600.0, max_frames=10)
    assert len(secs) == 10
    assert secs[0] >= 0 and secs[-1] < 600
    assert secs == sorted(secs)


def test_even_frame_seconds_handles_zero_duration():
    assert frames.even_frame_seconds(duration=0.0, max_frames=10) == [0.0]
