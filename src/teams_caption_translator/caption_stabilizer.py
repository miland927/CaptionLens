from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Iterable, Protocol

from .text_utils import normalize_text, similarity


class CaptionLike(Protocol):
    speaker: str
    text: str
    stable: bool


@dataclass
class StableCaption:
    speaker: str
    text: str
    frame_timestamp: float
    ocr_ms: float
    ocr_engine: str


@dataclass
class _PendingCaption:
    speaker: str
    text: str
    first_seen: float
    last_changed: float
    last_seen: float
    frame_timestamp: float
    ocr_ms: float
    ocr_engine: str


class CaptionStabilizer:
    """Merge rolling Teams OCR updates into stable, once-only captions.

    Teams captions are a moving transcript window: the same sentence appears on
    several screenshots while it slowly moves upward. Translating every OCR
    result wastes tokens and produces repeated, fragmented output. This class
    keeps a small per-speaker pending caption and only releases it after it has
    stopped changing briefly, or after it clearly ends with punctuation.
    """

    def __init__(
        self,
        hold_seconds: float = 1.0,
        min_chars: int = 4,
        emitted_ttl: int = 160,
        fuzzy_threshold: float = 0.92,
    ) -> None:
        self.hold_seconds = max(0.1, hold_seconds)
        self.min_chars = max(1, min_chars)
        self.emitted_ttl = max(20, emitted_ttl)
        self.fuzzy_threshold = fuzzy_threshold
        self._pending: dict[str, _PendingCaption] = {}
        self._emitted: list[tuple[str, str]] = []

    def update(
        self,
        entries: Iterable[CaptionLike],
        frame_timestamp: float,
        ocr_ms: float,
        ocr_engine: str,
        now: float | None = None,
    ) -> list[StableCaption]:
        now = monotonic() if now is None else now
        ready: list[StableCaption] = []
        seen_speakers: set[str] = set()

        for entry in entries:
            speaker = normalize_text(entry.speaker)
            text = normalize_text(entry.text)
            if not speaker or len(text) < self.min_chars or self._was_emitted(speaker, text):
                continue
            seen_speakers.add(speaker)
            flushed = self._merge_or_replace(speaker, text, frame_timestamp, ocr_ms, ocr_engine, now)
            if flushed is not None:
                ready.append(flushed)

        for speaker in list(self._pending):
            pending = self._pending[speaker]
            if speaker not in seen_speakers and self._is_ready(pending, now):
                ready.append(self._emit(speaker))
                continue
            if speaker in seen_speakers and self._is_ready(pending, now):
                ready.append(self._emit(speaker))

        return [item for item in ready if item is not None]

    def flush(self) -> list[StableCaption]:
        ready = [self._emit(speaker) for speaker in list(self._pending)]
        return [item for item in ready if item is not None]

    def _merge_or_replace(
        self,
        speaker: str,
        text: str,
        frame_timestamp: float,
        ocr_ms: float,
        ocr_engine: str,
        now: float,
    ) -> StableCaption | None:
        pending = self._pending.get(speaker)
        if pending is None:
            self._pending[speaker] = _PendingCaption(
                speaker=speaker,
                text=text,
                first_seen=now,
                last_changed=now,
                last_seen=now,
                frame_timestamp=frame_timestamp,
                ocr_ms=ocr_ms,
                ocr_engine=ocr_engine,
            )
            return None

        relation = _text_relation(pending.text, text)
        if relation in {"same", "extends", "similar"}:
            if relation == "extends" or len(text) > len(pending.text):
                pending.text = text
                pending.last_changed = now
            pending.last_seen = now
            pending.frame_timestamp = frame_timestamp
            pending.ocr_ms = ocr_ms
            pending.ocr_engine = ocr_engine
            return None

        flushed: StableCaption | None = None
        if self._is_ready(pending, now):
            flushed = self._emit(speaker)
        self._pending[speaker] = _PendingCaption(
            speaker=speaker,
            text=text,
            first_seen=now,
            last_changed=now,
            last_seen=now,
            frame_timestamp=frame_timestamp,
            ocr_ms=ocr_ms,
            ocr_engine=ocr_engine,
        )
        return flushed

    def _is_ready(self, pending: _PendingCaption, now: float) -> bool:
        unchanged_for = now - pending.last_changed
        seen_for = now - pending.first_seen
        if _looks_complete(pending.text) and unchanged_for >= self.hold_seconds * 0.45:
            return True
        return seen_for >= self.hold_seconds and unchanged_for >= self.hold_seconds * 0.5

    def _emit(self, speaker: str) -> StableCaption | None:
        pending = self._pending.pop(speaker, None)
        if pending is None:
            return None
        if self._was_emitted(pending.speaker, pending.text):
            return None
        self._emitted.append((pending.speaker, pending.text))
        self._emitted = self._emitted[-self.emitted_ttl :]
        return StableCaption(
            speaker=pending.speaker,
            text=pending.text,
            frame_timestamp=pending.frame_timestamp,
            ocr_ms=pending.ocr_ms,
            ocr_engine=pending.ocr_engine,
        )

    def _was_emitted(self, speaker: str, text: str) -> bool:
        normalized = normalize_text(text)
        for old_speaker, old_text in self._emitted:
            if old_speaker != speaker:
                continue
            old = normalize_text(old_text)
            if normalized == old:
                return True
            if len(normalized) >= 8 and (normalized in old or old in normalized):
                return True
            if similarity(normalized, old) >= self.fuzzy_threshold:
                return True
        return False


def _text_relation(old: str, new: str) -> str:
    old = normalize_text(old)
    new = normalize_text(new)
    if old == new:
        return "same"
    if old and old in new:
        return "extends"
    if new and new in old:
        return "same"
    if similarity(old, new) >= 0.78:
        return "similar"
    return "different"


def _looks_complete(text: str) -> bool:
    text = normalize_text(text)
    if not text:
        return False
    return text.endswith(("。", ".", "！", "!", "？", "?", "です", "ます", "でした", "ました"))
