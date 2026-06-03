from teams_caption_translator.pipeline import format_caption_entry, normalize_ocr_text, parse_caption_entries


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
