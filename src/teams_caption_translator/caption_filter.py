from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Protocol

from .text_utils import normalize_text


class CaptionEntryLike(Protocol):
    speaker: str
    text: str
    stable: bool


@dataclass
class CaptionQuality:
    accepted: bool
    reason: str = ""


_DATE_OR_TIME_RE = re.compile(
    r"^(?:\d{1,4}[./-]\d{1,2}(?:[./-]\d{1,2})?|\d{1,2}月\d{1,2}日|\d{1,2}[:：.]\d{2})$"
)
_NUMERIC_LINE_RE = re.compile(r"^[\d\s:：./年月日分秒%％()\[\]（）<>＜＞+\-−~〜,，.]+$")
_INTERNAL_SPEAKER_RE = re.compile(r"^[「『《<\[]?\s*[^:：\s]{1,18}\s*[:：]\s*\d{1,4}\s*[」』》>\]]?$")


def filter_caption_entries(entries: Iterable[CaptionEntryLike]) -> list[CaptionEntryLike]:
    return [entry for entry in entries if caption_quality(entry.speaker, entry.text).accepted]


def caption_quality(speaker: str, text: str) -> CaptionQuality:
    speaker = normalize_speaker_label(speaker)
    text = normalize_text(text)
    if not speaker:
        return CaptionQuality(False, "empty speaker")
    if not text:
        return CaptionQuality(False, "empty text")
    if _looks_like_bad_speaker(speaker):
        return CaptionQuality(False, "bad speaker label")
    if _looks_like_metadata(text):
        return CaptionQuality(False, "metadata")
    if _looks_like_ocr_gibberish(text):
        return CaptionQuality(False, "low Japanese ratio")
    return CaptionQuality(True)


def normalize_speaker_label(speaker: str) -> str:
    speaker = normalize_text(speaker)
    speaker = speaker.strip(" -*\t\r\n")
    speaker = speaker.strip("「」『』《》<>[]【】")
    speaker = speaker.replace("*", "").strip()
    speaker = re.sub(r"\s+", " ", speaker)
    return speaker


def _looks_like_bad_speaker(speaker: str) -> bool:
    speaker = normalize_speaker_label(speaker)
    if not speaker:
        return True
    if _INTERNAL_SPEAKER_RE.match(speaker):
        return True
    if speaker[0].isdigit():
        return True
    if len(speaker) <= 5 and speaker.isascii() and speaker.isupper():
        return True
    if len(speaker) > 28:
        return True
    if any(mark in speaker for mark in "。、，,！？!?()（）"):
        return True
    return False


def _looks_like_metadata(text: str) -> bool:
    compact = normalize_text(text).replace(" ", "")
    if not compact:
        return True
    if _DATE_OR_TIME_RE.match(compact):
        return True
    if _NUMERIC_LINE_RE.match(compact):
        return True

    digit_count = sum(char.isdigit() for char in compact)
    meaningful_count = sum(_is_japanese_or_cjk(char) or char.isalpha() for char in compact)
    if len(compact) <= 12 and digit_count >= 2 and digit_count >= meaningful_count:
        return True
    return False


def _looks_like_ocr_gibberish(text: str) -> bool:
    compact = normalize_text(text).replace(" ", "")
    if len(compact) < 6:
        return False

    japanese_count = sum(_is_japanese_or_cjk(char) for char in compact)
    latin_count = sum("a" <= char.lower() <= "z" for char in compact)
    digit_count = sum(char.isdigit() for char in compact)
    symbol_count = sum(not char.isalnum() and not _is_japanese_or_cjk(char) for char in compact)
    content_count = japanese_count + latin_count + digit_count
    if content_count == 0:
        return True

    if latin_count and any(mark in compact for mark in ("ヽ", "ヾ", "ゝ", "ゞ", "|")):
        return True

    japanese_ratio = japanese_count / max(1, content_count)
    symbol_ratio = symbol_count / max(1, len(compact))
    if japanese_ratio < 0.35 and symbol_ratio > 0.20:
        return True
    if japanese_ratio < 0.25 and latin_count + digit_count >= japanese_count:
        return True
    return False


def _is_japanese_or_cjk(char: str) -> bool:
    return (
        "\u3040" <= char <= "\u309f"
        or "\u30a0" <= char <= "\u30ff"
        or "\u3400" <= char <= "\u4dbf"
        or "\u4e00" <= char <= "\u9fff"
    )
