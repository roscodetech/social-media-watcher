import tiktok_watch


def test_needs_even_sampling_when_too_few_scene_frames():
    assert tiktok_watch.needs_even_sampling(0) is True
    assert tiktok_watch.needs_even_sampling(3) is True


def test_needs_even_sampling_false_when_enough_frames():
    assert tiktok_watch.needs_even_sampling(4) is False
    assert tiktok_watch.needs_even_sampling(20) is False


def test_evenly_spaced_indices_returns_all_when_under_cap():
    assert tiktok_watch.evenly_spaced_indices(5, 14) == [0, 1, 2, 3, 4]


def test_evenly_spaced_indices_downsamples_when_over_cap():
    result = tiktok_watch.evenly_spaced_indices(100, 10)
    assert len(result) == 10
    assert result[0] == 0
    assert result == sorted(result)
    assert max(result) <= 99


def test_evenly_spaced_indices_handles_empty_and_zero():
    assert tiktok_watch.evenly_spaced_indices(0, 14) == []
    assert tiktok_watch.evenly_spaced_indices(10, 0) == []
