from teams_caption_translator.text_utils import RecentTextCache, normalize_text, similarity


def test_normalize_text_collapses_spaces():
    assert normalize_text("  ｱ  \n  test\u3000value ") == "ア test value"


def test_similarity_identical():
    assert similarity("hello", "hello") == 1.0


def test_recent_text_cache_uses_fuzzy_match():
    cache = RecentTextCache(fuzzy_threshold=0.8)
    assert cache.seen("今日はいい天気です") is False
    assert cache.seen("今日は いい天気です") is True
