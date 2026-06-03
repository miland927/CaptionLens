from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
from threading import Event, Thread
from time import monotonic, perf_counter, sleep

from PIL import Image, ImageChops, ImageStat

from .capture import CapturedFrame, create_capture_backend
from .config import AppConfig
from .ocr import create_ocr_backend
from .text_utils import RecentTextCache, normalize_text, similarity
from .translator import create_translator


@dataclass
class PipelineEvent:
    kind: str
    raw_text: str = ""
    translated_text: str = ""
    detail: str = ""
    capture_ms: float = 0.0
    ocr_ms: float = 0.0
    translation_ms: float = 0.0
    total_ms: float = 0.0


@dataclass
class CaptionEntry:
    speaker: str
    text: str
    stable: bool = True


class LatestQueue:
    def __init__(self) -> None:
        self._queue: Queue = Queue(maxsize=1)

    def put(self, item) -> None:
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except Empty:
                pass
        self._queue.put_nowait(item)

    def get(self, timeout: float = 0.1):
        return self._queue.get(timeout=timeout)


class CaptionPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.events: Queue[PipelineEvent] = Queue()
        self._frames = LatestQueue()
        self._ocr_text = LatestQueue()
        self._stop = Event()
        self._threads: list[Thread] = []

    def start(self) -> None:
        self._stop.clear()
        for target, name in (
            (self._capture_loop, "capture"),
            (self._ocr_loop, "ocr"),
            (self._translation_loop, "translation"),
        ):
            thread = Thread(target=target, name=f"caption-{name}", daemon=True)
            self._threads.append(thread)
            thread.start()

    def stop(self) -> None:
        self._stop.set()
        for thread in self._threads:
            thread.join(timeout=1.0)
        self._threads.clear()

    def _capture_loop(self) -> None:
        if not self.config.region.is_ready:
            self.events.put(PipelineEvent("error", detail="No capture region selected."))
            return
        backend = create_capture_backend()
        last_image = None
        stable_count = 0
        last_emit = 0.0
        last_status = 0.0
        min_interval = 1.0 / max(self.config.capture_fps, 1)
        min_ocr_interval = 0.9
        try:
            while not self._stop.is_set():
                tick = perf_counter()
                frame = backend.grab(self.config.region)
                delta = image_delta(last_image, frame.image) if last_image is not None else 999.0
                last_image = frame.image
                if delta >= self.config.change_threshold:
                    stable_count = 0
                else:
                    stable_count += 1

                if stable_count >= self.config.stable_frames and monotonic() - last_emit > min_ocr_interval:
                    self._frames.put(frame)
                    last_emit = monotonic()

                now = monotonic()
                if now - last_status > 1.2:
                    last_status = now
                    self.events.put(
                        PipelineEvent(
                            "capture",
                            detail=f"capturing: {backend.name}; delta {delta:.1f}; stable {stable_count}",
                        )
                    )

                elapsed = perf_counter() - tick
                sleep(max(0.0, min_interval - elapsed))
        except Exception as exc:
            self.events.put(PipelineEvent("error", detail=f"Capture failed: {exc}"))
        finally:
            backend.close()

    def _ocr_loop(self) -> None:
        self.events.put(PipelineEvent("loading", detail="Loading OCR engine..."))
        backend = create_ocr_backend(self.config.ocr_lang, self.config.ocr_provider)
        self.events.put(PipelineEvent("loading", detail=f"OCR engine ready: {backend.name}"))
        last_text = ""
        last_empty_notice = 0.0
        last_error_notice = 0.0
        while not self._stop.is_set():
            try:
                frame: CapturedFrame = self._frames.get(timeout=0.2)
            except Empty:
                continue
            started = perf_counter()
            try:
                text = normalize_ocr_text(backend.recognize(frame.image))
                ocr_ms = (perf_counter() - started) * 1000
                if text and similarity(text, last_text) < 0.985:
                    last_text = text
                    preview_entries = parse_caption_entries(text)
                    preview_lines = [format_caption_entry(entry.speaker, entry.text) for entry in ([e for e in preview_entries if e.stable] or preview_entries)]
                    if preview_lines:
                        self.events.put(
                            PipelineEvent(
                                "ocr_text",
                                raw_text="\n\n".join(preview_lines),
                                detail=f"OCR: {backend.name}",
                                ocr_ms=ocr_ms,
                            )
                        )
                    self._ocr_text.put((text, frame.timestamp, ocr_ms, backend.name))
                elif not text:
                    now = monotonic()
                    if now - last_empty_notice > 2.0:
                        last_empty_notice = now
                        self.events.put(PipelineEvent("empty", detail=f"OCR engine: {backend.name}", ocr_ms=ocr_ms))
            except Exception as exc:
                now = monotonic()
                if now - last_error_notice > 2.0:
                    last_error_notice = now
                    self.events.put(PipelineEvent("error", detail=f"OCR failed: {exc}"))

    def _translation_loop(self) -> None:
        try:
            translator = create_translator(self.config.translator, self.config.deepseek_api_key)
        except Exception as exc:
            self.events.put(PipelineEvent("error", detail=f"翻译器启动失败: {exc}"))
            return
        self.events.put(PipelineEvent("loading", detail=f"翻译器已就绪: {translator.provider}"))
        recent = RecentTextCache(fuzzy_threshold=0.90)
        context: list[str] = []
        while not self._stop.is_set():
            try:
                text, frame_timestamp, ocr_ms, ocr_engine = self._ocr_text.get(timeout=0.2)
            except Empty:
                continue
            entries = parse_caption_entries(text)
            stable_entries = [entry for entry in entries if entry.stable]
            for entry in stable_entries or entries:
                normalized_entry = normalize_text(f"{entry.speaker}:{entry.text}")
                if not entry.text or recent.seen(normalized_entry):
                    continue
                started = perf_counter()
                try:
                    result = translator.translate(entry.text, self.config.source_lang, self.config.target_lang, context)
                    translation_ms = (perf_counter() - started) * 1000
                    raw_line = format_caption_entry(entry.speaker, entry.text)
                    translated_line = format_caption_entry(entry.speaker, result.text)
                    context.append(entry.text)
                    context[:] = context[-5:]
                    self.events.put(
                        PipelineEvent(
                            "result",
                            raw_text=raw_line,
                            translated_text=translated_line,
                            detail=f"OCR: {ocr_engine}; translator: {result.provider}",
                            ocr_ms=ocr_ms,
                            translation_ms=translation_ms,
                            total_ms=(perf_counter() - frame_timestamp) * 1000,
                        )
                    )
                except Exception as exc:
                    self.events.put(PipelineEvent("error", raw_text=entry.text, detail=f"Translation failed: {exc}"))


def image_delta(a: Image.Image | None, b: Image.Image) -> float:
    if a is None:
        return 999.0
    if a.size != b.size:
        b = b.resize(a.size)
    a_small = a.convert("L").resize((64, 36))
    b_small = b.convert("L").resize((64, 36))
    diff = ImageChops.difference(a_small, b_small)
    return float(ImageStat.Stat(diff).mean[0])


def parse_caption_entries(text: str) -> list[CaptionEntry]:
    lines = [_clean_caption_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]
    entries: list[CaptionEntry] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if "：" in line or ":" in line:
            sep = "：" if "：" in line else ":"
            left, right = line.split(sep, 1)
            if left.strip() and right.strip():
                entries.append(CaptionEntry(_clean_speaker(left), right.strip(), stable=True))
                index += 1
                continue

        if not _looks_like_speaker(line):
            index += 1
            continue

        speaker = _clean_speaker(line)
        index += 1
        content_lines: list[str] = []
        while index < len(lines) and not _looks_like_speaker(lines[index]):
            content_lines.append(lines[index])
            index += 1
        if content_lines:
            content = " ".join(content_lines)
            stable = index < len(lines) or _looks_complete_caption(content, len(content_lines))
            entries.append(CaptionEntry(speaker, content, stable=stable))
    return entries


def normalize_ocr_text(text: str) -> str:
    lines = [normalize_text(line) for line in (text or "").splitlines()]
    return "\n".join(line for line in lines if line)


def format_caption_entry(speaker: str, text: str) -> str:
    speaker = _clean_speaker(speaker) or "字幕"
    return f"{speaker}：{text.strip()}"


def _clean_caption_line(line: str) -> str:
    line = line.strip()
    noise = ("通話保留", "ミュート", "字幕", "Teams")
    if any(token == line for token in noise):
        return ""
    if _looks_like_avatar_label(line):
        return ""
    return line


def _clean_speaker(speaker: str) -> str:
    return speaker.replace("*", "").strip(" -*\t")


def _looks_like_speaker(line: str) -> bool:
    if len(line) > 28:
        return False
    if _looks_like_avatar_label(line):
        return False
    if any(mark in line for mark in "。、，,！？!?「」()（）"):
        return False
    return any(char.isalpha() or "\u3040" <= char <= "\u30ff" or "\u4e00" <= char <= "\u9fff" for char in line)


def _looks_like_avatar_label(line: str) -> bool:
    if len(line) > 5:
        return False
    if line.endswith("F") and line[:-1].isdigit():
        return True
    return line.isupper() and line.isascii()


def _looks_complete_caption(text: str, line_count: int) -> bool:
    text = text.rstrip()
    if text.endswith(("。", ".", "！", "!", "？", "?")):
        return True
    if line_count >= 2:
        return True
    return text.endswith(("です", "ます", "ですね", "ました", "でした"))
