from teams_caption_translator.pipeline import (
    format_caption_entry,
    latest_caption_segments,
    normalize_ocr_text,
    parse_caption_entries,
    split_caption_segments,
)


def test_parse_caption_entries_uses_speaker_line():
    text = normalize_ocr_text("藤田 悠介 *\nなるほど、そういうことです。\n吉 天一\n分かりました。")

    entries = parse_caption_entries(text)

    assert format_caption_entry(entries[0].speaker, entries[0].text) == "藤田 悠介：なるほど、そういうことです。"
    assert format_caption_entry(entries[1].speaker, entries[1].text) == "吉 天一：分かりました。"


def test_parse_caption_entries_keeps_colon_format():
    entries = parse_caption_entries("Speaker A: hello")

    assert format_caption_entry(entries[0].speaker, entries[0].text) == "Speaker A：hello"


def test_parse_caption_entries_groups_teams_scrolling_captions():
    text = normalize_ocr_text(
        "10F\n"
        "PC教務事務1\n"
        "そうすると、ええ、この小売りモデルはですね。\n"
        "まずデスティネーション型のモデルで、顧客がですね。\n"
        "10F\n"
        "PC教務事務1\n"
        "すなわち、自社がですね、直接収集したデータですね。"
    )

    entries = parse_caption_entries(text)

    assert len(entries) == 2
    assert entries[0].speaker == "PC教務事務1"
    assert entries[0].text == "そうすると、ええ、この小売りモデルはですね。 まずデスティネーション型のモデルで、顧客がですね。"
    assert entries[1].speaker == "PC教務事務1"
    assert entries[1].text == "すなわち、自社がですね、直接収集したデータですね。"


def test_parse_caption_entries_skips_unfinished_bottom_entry():
    text = normalize_ocr_text("10F\nPC教務事務1\nできるか、あるいはイバリエーション型のモデルで")

    entries = parse_caption_entries(text)

    assert len(entries) == 1
    assert entries[0].stable is False


def test_split_caption_segments_keeps_scroll_updates_sentence_sized():
    segments = split_caption_segments(
        "時にあのまあ全部個別配当のものを、人数で入れておりましたので。"
        "あのですね。"
        "えっと分析方法ですね。"
    )

    assert segments == [
        "時にあのまあ全部個別配当のものを、人数で入れておりましたので。",
        "あのですね。",
        "えっと分析方法ですね。",
    ]


def test_parse_caption_entries_groups_speaker_with_wrapped_lines():
    text = normalize_ocr_text(
        "富山 栄子\n"
        "ちょっと四番はその調査結果もちょっと分析の方法のものなんですけど、\n"
        "ここがまだ十分にかけてないです。\n"
        "王\n"
        "はい。"
    )

    entries = parse_caption_entries(text)

    assert format_caption_entry(entries[0].speaker, entries[0].text) == (
        "富山 栄子：ちょっと四番はその調査結果もちょっと分析の方法のものなんですけど、 ここがまだ十分にかけてないです。"
    )
    assert format_caption_entry(entries[1].speaker, entries[1].text) == "王：はい。"


def test_latest_caption_segments_prefers_newest_visible_captions():
    entries = parse_caption_entries(
        normalize_ocr_text(
            "富山栄子\n"
            "一番古いです。\n"
            "富山栄子\n"
            "少し新しいです。\n"
            "富山栄子\n"
            "一番新しいです。"
        )
    )

    latest = latest_caption_segments(entries, max_segments=2)

    assert [segment for _entry, segment in latest] == ["少し新しいです。", "一番新しいです。"]
