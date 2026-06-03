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
        self.language = language
        handle = tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8")
        handle.write(_PS_OCR_SCRIPT)
        handle.close()
        self._script_path = Path(handle.name)

    def recognize(self, image: Image.Image) -> str:
        prepared = preprocess_for_ocr(image)
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
                text=True,
                timeout=8,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "Windows OCR failed")
            return result.stdout.strip()
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


class EasyOcrBackend:
    name = "easyocr"

    def __init__(self, language: str) -> None:
        import easyocr

        lang = "ja" if language.lower().startswith("ja") else language.split("-")[0].lower()
        self._reader = easyocr.Reader([lang], gpu=False, download_enabled=False)

    def recognize(self, image: Image.Image) -> str:
        import numpy as np

        result = self._reader.readtext(np.array(image.convert("RGB")), detail=0, paragraph=True)
        if not result:
            return ""
        return "\n".join(str(line) for line in result)


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


def create_ocr_backend(language: str, provider: str = "auto") -> OcrBackend:
    if provider == "auto":
        backends: list[OcrBackend] = []
        for candidate in ("windows", "easyocr", "rapidocr"):
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
