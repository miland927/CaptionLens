from __future__ import annotations

from difflib import SequenceMatcher
import re
import time
import unicodedata


_SPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\u3000", " ")
    text = _SPACE_RE.sub(" ", text)
    return text.strip()


def similarity(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


class RecentTextCache:
    def __init__(self, ttl_seconds: float = 120.0, fuzzy_threshold: float = 0.94) -> None:
        self.ttl_seconds = ttl_seconds
        self.fuzzy_threshold = fuzzy_threshold
        self._items: list[tuple[float, str]] = []

    def seen(self, text: str) -> bool:
        now = time.monotonic()
        self._items = [(t, v) for t, v in self._items if now - t < self.ttl_seconds]
        if any(similarity(text, old) >= self.fuzzy_threshold for _, old in self._items):
            return True
        self._items.append((now, text))
        return False
