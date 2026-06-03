from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Protocol

from PIL import Image, ImageFilter, ImageOps


@dataclass
class OcrResult:
    text: str
    engine: str
    latency_ms: float


class OcrBackend(Protocol):
    name: str

    def recognize(self, image: Image.Image) -> str:
        ...


class OcrUnavailableError(RuntimeError):
    pass


_PS_OCR_SCRIPT = r"""
param([string]$imgPath, [string]$lang)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Foundation, ContentType=WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Foundation, ContentType=WindowsRuntime]
function Await($op) {
    $task = [System.WindowsRuntimeSystemExtensions]::AsTask($op)
    $task.Wait() | Out-Null
    $task.Result
}
$langObj = [Windows.Globalization.Language]::new($lang)
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($langObj)
if (-not $engine) { Write-Error "OCR engine not available for language: $lang"; exit 1 }
$file = Await([Windows.Storage.StorageFile]::GetFileFromPathAsync($imgPath))
$stream = Await($file.OpenAsync([Windows.Storage.FileAccessMode]::Read))
$decoder = Await([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream))
$bmp = Await($decoder.GetSoftwareBitmapAsync())
$result = Await($engine.RecognizeAsync($bmp))
$result.Text
"""


class WindowsPowerShellOcr:
    name = "windows-ocr-powershell"

    def __init__(self, language: str) -> None:
        self.language = _windows_ocr_language(language)
        handle = tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8")
        handle.write(_PS_OCR_SCRIPT)
        handle.close()
        self._script_path = Path(handle.name)

    def recognize(self, image: Image.Image) -> str:
        prepared = preprocess_for_windows_ocr(image)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            image_path = Path(handle.name)
        try:
            prepared.save(image_path, "PNG")
            startupinfo = None
            creationflags = 0
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            result = subprocess.run(
                [
                    "powershell",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(self._script_path),
                    "-imgPath",
                    str(image_path),
                    "-lang",
                    self.language,
                ],
                capture_output=True,
                timeout=8,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
            if result.returncode != 0:
                raise RuntimeError(_decode_process_output(result.stderr).strip() or "Windows OCR failed")
            return _decode_process_output(result.stdout).strip()
        finally:
            image_path.unlink(missing_ok=True)


class RapidOcrBackend:
    name = "rapidocr"

    def __init__(self) -> None:
        from rapidocr_onnxruntime import RapidOCR

        self._engine = RapidOCR()

    def recognize(self, image: Image.Image) -> str:
        result, _ = self._engine(preprocess_for_ocr(image))
        if not result:
            return ""
        return "\n".join(str(item[1]) for item in result if len(item) >= 2)


def _decode_process_output(data: bytes) -> str:
    candidates = []
    for encoding in ("utf-8-sig", "cp932", "utf-16", "utf-16le", "mbcs"):
        try:
            text = data.decode(encoding, errors="replace")
        except LookupError:
            continue
        candidates.append((_japanese_score(text), text))
    if not candidates:
        return data.decode(errors="replace")
    return max(candidates, key=lambda item: item[0])[1]


def _japanese_score(text: str) -> int:
    score = 0
    for char in text:
        if "\u3040" <= char <= "\u30ff" or "\u4e00" <= char <= "\u9fff":
            score += 3
        elif char == "\ufffd":
            score -= 5
        elif char.isprintable():
            score += 1
    return score


def _looks_like_garbage(text: str) -> bool:
    chars = [char for char in text if not char.isspace()]
    if not chars:
        return False
    replacement_count = text.count("\ufffd")
    japanese_count = sum(1 for char in chars if "\u3040" <= char <= "\u30ff" or "\u4e00" <= char <= "\u9fff")
    return replacement_count >= 3 and replacement_count > japanese_count


def _ocr_text_quality_score(text: str) -> int:
    score = 0
    for char in text:
        if "\u3040" <= char <= "\u30ff" or "\u4e00" <= char <= "\u9fff":
            score += 4
        elif char == "\ufffd":
            score -= 8
        elif "\u00c0" <= char <= "\u024f":
            score -= 3
        elif char.isprintable():
            score += 1
    return score


def _windows_ocr_language(language: str) -> str:
    mapping = {
        "ja": "ja-JP",
        "jp": "ja-JP",
        "en": "en-US",
        "ko": "ko-KR",
        "zh-cn": "zh-CN",
        "zh-tw": "zh-TW",
    }
    return mapping.get(language.lower(), language)


class EasyOcrBackend:
    name = "easyocr"

    def __init__(self, language: str) -> None:
        import easyocr

        lang = "ja" if language.lower().startswith("ja") else language.split("-")[0].lower()
        self._reader = easyocr.Reader([lang], gpu=False, download_enabled=False)

    def recognize(self, image: Image.Image) -> str:
        import numpy as np

        best_text = ""
        best_score = -10**9
        for prepared in preprocess_variants_for_easyocr(image):
            result = self._reader.readtext(
                np.array(prepared),
                detail=0,
                paragraph=False,
                decoder="greedy",
                text_threshold=0.4,
                low_text=0.2,
                mag_ratio=1.5,
            )
            text = "\n".join(str(line) for line in result) if result else ""
            score = _ocr_text_quality_score(text)
            if score > best_score:
                best_text = text
                best_score = score
        return best_text


class NullOcr:
    name = "no-ocr"

    def recognize(self, image: Image.Image) -> str:
        return ""


class FallbackOcrBackend:
    name = "auto"

    def __init__(self, backends: list[OcrBackend]) -> None:
        self.backends = backends
        self.name = "auto(" + " -> ".join(backend.name for backend in backends) + ")"

    def recognize(self, image: Image.Image) -> str:
        errors: list[str] = []
        for backend in self.backends:
            try:
                text = backend.recognize(image).strip()
            except Exception as exc:
                errors.append(f"{backend.name}: {exc}")
                continue
            if _looks_like_garbage(text):
                errors.append(f"{backend.name}: 识别结果乱码")
                continue
            if text:
                self.name = backend.name
                return text
        if errors:
            raise OcrUnavailableError("；".join(errors))
        return ""


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image)
    w, h = gray.size
    if w < 1200:
        scale = max(1, min(3, round(1200 / max(w, 1))))
        gray = gray.resize((w * scale, h * scale), Image.LANCZOS)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = gray.filter(ImageFilter.SHARPEN)

    histogram = gray.histogram()
    total = sum(histogram) or 1

    def percentile(percent: float) -> int:
        target = total * percent
        acc = 0
        for value, count in enumerate(histogram):
            acc += count
            if acc >= target:
                return value
        return 255

    low = percentile(0.10)
    median = percentile(0.50)
    high = percentile(0.90)
    threshold = int((low + high) / 2) if high - low >= 35 else 128

    # Teams captions are usually light text on a dark translucent band. The
    # inverted branch keeps black text on light screenshots readable too.
    if median < 128:
        return gray.point(lambda p: 255 if p >= threshold else 0)
    return gray.point(lambda p: 0 if p >= threshold else 255)


def preprocess_for_windows_ocr(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    w, h = rgb.size
    if w < 1400:
        scale = max(1, min(3, round(1400 / max(w, 1))))
        rgb = rgb.resize((w * scale, h * scale), Image.LANCZOS)
    gray = ImageOps.grayscale(rgb)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    return gray.convert("RGB")


def preprocess_for_easyocr(image: Image.Image) -> Image.Image:
    return preprocess_variants_for_easyocr(image)[0]


def preprocess_variants_for_easyocr(image: Image.Image) -> list[Image.Image]:
    rgb = image.convert("RGB")
    w, h = rgb.size
    if h > 320:
        rgb = rgb.crop((0, min(100, h // 4), w, h))
        w, h = rgb.size

    variants: list[Image.Image] = []
    scale = 2 if w < 2200 else 1
    scaled = rgb.resize((w * scale, h * scale), Image.LANCZOS) if scale > 1 else rgb
    variants.append(scaled)
    gray = ImageOps.grayscale(rgb)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray_rgb = gray.resize((w * scale, h * scale), Image.LANCZOS).convert("RGB") if scale > 1 else gray.convert("RGB")
    variants.append(gray_rgb)
    return variants


def create_ocr_backend(language: str, provider: str = "auto") -> OcrBackend:
    if provider == "auto":
        backends: list[OcrBackend] = []
        candidates = ("windows", "easyocr", "rapidocr")
        for candidate in candidates:
            backend = create_ocr_backend(language, candidate)
            if not isinstance(backend, NullOcr):
                backends.append(backend)
        return FallbackOcrBackend(backends) if backends else NullOcr()

    # Windows built-in OCR is zero-dependency and fast when the OCR language is installed.
    if provider == "windows":
        try:
            return WindowsPowerShellOcr(language)
        except Exception:
            pass
    if provider == "easyocr":
        try:
            return EasyOcrBackend(language)
        except Exception:
            pass
    if provider == "rapidocr":
        try:
            return RapidOcrBackend()
        except Exception:
            pass
    return NullOcr()
