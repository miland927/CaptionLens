from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from PIL import Image

from .config import Region


@dataclass
class CapturedFrame:
    image: Image.Image
    timestamp: float


class CaptureBackend(Protocol):
    name: str

    def grab(self, region: Region) -> CapturedFrame:
        ...

    def close(self) -> None:
        ...


class MssCapture:
    name = "mss"

    def __init__(self) -> None:
        from mss import mss

        self._mss = mss()

    def grab(self, region: Region) -> CapturedFrame:
        monitor = {"left": region.x, "top": region.y, "width": region.w, "height": region.h}
        shot = self._mss.grab(monitor)
        image = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        return CapturedFrame(image=image, timestamp=perf_counter())

    def close(self) -> None:
        self._mss.close()


class ImageGrabCapture:
    name = "pillow-imagegrab"

    def grab(self, region: Region) -> CapturedFrame:
        from PIL import ImageGrab

        bbox = (region.x, region.y, region.x + region.w, region.y + region.h)
        return CapturedFrame(image=ImageGrab.grab(bbox=bbox), timestamp=perf_counter())

    def close(self) -> None:
        return None


def create_capture_backend() -> CaptureBackend:
    try:
        return MssCapture()
    except Exception:
        return ImageGrabCapture()
