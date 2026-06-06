from dataclasses import dataclass

from teams_caption_translator.caption_stabilizer import CaptionStabilizer


@dataclass
class Entry:
    speaker: str
    text: str
    stable: bool = True


def test_stabilizer_waits_before_emitting_caption():
    stabilizer = CaptionStabilizer(hold_seconds=1.0)

    assert stabilizer.update([Entry("Speaker", "short phrase")], 0.0, 10.0, "ocr", now=0.0) == []
    assert stabilizer.update([Entry("Speaker", "short phrase")], 0.0, 10.0, "ocr", now=0.4) == []

    ready = stabilizer.update([Entry("Speaker", "short phrase")], 0.0, 10.0, "ocr", now=1.1)

    assert [(item.speaker, item.text) for item in ready] == [("Speaker", "short phrase")]


def test_stabilizer_merges_scrolling_caption_extensions():
    stabilizer = CaptionStabilizer(hold_seconds=1.0)

    stabilizer.update([Entry("Speaker", "from OCR")], 0.0, 10.0, "ocr", now=0.0)
    stabilizer.update([Entry("Speaker", "from OCR and more.")], 0.2, 10.0, "ocr", now=0.2)
    ready = stabilizer.update([Entry("Speaker", "from OCR and more.")], 0.4, 10.0, "ocr", now=0.8)

    assert [(item.speaker, item.text) for item in ready] == [("Speaker", "from OCR and more.")]


def test_stabilizer_does_not_emit_duplicate_visible_caption():
    stabilizer = CaptionStabilizer(hold_seconds=0.5)

    stabilizer.update([Entry("Speaker", "same sentence.")], 0.0, 10.0, "ocr", now=0.0)
    first = stabilizer.update([Entry("Speaker", "same sentence.")], 0.4, 10.0, "ocr", now=0.4)
    second = stabilizer.update([Entry("Speaker", "same sentence.")], 1.0, 10.0, "ocr", now=1.0)
    third = stabilizer.update([Entry("Speaker", "same sentence.")], 2.0, 10.0, "ocr", now=2.0)

    assert [(item.speaker, item.text) for item in first] == [("Speaker", "same sentence.")]
    assert second == []
    assert third == []
