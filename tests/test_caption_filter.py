from dataclasses import dataclass

from teams_caption_translator.caption_filter import (
    caption_quality,
    filter_caption_entries,
    normalize_speaker_label,
)


@dataclass
class Entry:
    speaker: str
    text: str
    stable: bool = True


def test_filter_rejects_dates_scores_and_numeric_metadata():
    entries = [
        Entry("柄守敏", "05月14日"),
        Entry("隊字軒", "13.37"),
        Entry("富山 栄子", "試算表を作成しました。"),
    ]

    filtered = filter_caption_entries(entries)

    assert [(entry.speaker, entry.text) for entry in filtered] == [("富山 栄子", "試算表を作成しました。")]


def test_filter_rejects_digit_started_speaker_labels():
    assert caption_quality("10下", "每天重复这个？").accepted is False
    assert caption_quality("10F", "そうですね。").accepted is False


def test_filter_rejects_symbol_heavy_ocr_gibberish():
    assert caption_quality("富山 栄子", "ロ ヽ のIIカリ 転記をイた こトーか。").accepted is False


def test_filter_keeps_normal_japanese_caption():
    assert caption_quality("富山 栄子", "マトウィックも高いし、あとはまあそうですね。").accepted is True


def test_normalize_speaker_label_strips_wrappers_and_mute_marker():
    assert normalize_speaker_label("『教務事務1 *」") == "教務事務1"
