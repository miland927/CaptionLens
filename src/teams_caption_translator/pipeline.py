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
                text = normalize_text(backend.recognize(frame.image))
                ocr_ms = (perf_counter() - started) * 1000
                if text and similarity(text, last_text) < 0.985:
                    last_text = text
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
        recent = RecentTextCache()
        context: list[str] = []
        while not self._stop.is_set():
            try:
                text, frame_timestamp, ocr_ms, ocr_engine = self._ocr_text.get(timeout=0.2)
            except Empty:
                continue
            if recent.seen(text):
                continue
            started = perf_counter()
            try:
                result = translator.translate(text, self.config.source_lang, self.config.target_lang, context)
                translation_ms = (perf_counter() - started) * 1000
                context.append(text)
                context[:] = context[-5:]
                self.events.put(
                    PipelineEvent(
                        "result",
                        raw_text=text,
                        translated_text=result.text,
                        detail=f"OCR: {ocr_engine}; translator: {result.provider}",
                        ocr_ms=ocr_ms,
                        translation_ms=translation_ms,
                        total_ms=(perf_counter() - frame_timestamp) * 1000,
                    )
                )
            except Exception as exc:
                self.events.put(PipelineEvent("error", raw_text=text, detail=f"Translation failed: {exc}"))


def image_delta(a: Image.Image | None, b: Image.Image) -> float:
    if a is None:
        return 999.0
    if a.size != b.size:
        b = b.resize(a.size)
    a_small = a.convert("L").resize((64, 36))
    b_small = b.convert("L").resize((64, 36))
    diff = ImageChops.difference(a_small, b_small)
    return float(ImageStat.Stat(diff).mean[0])
