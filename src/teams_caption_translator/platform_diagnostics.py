from __future__ import annotations

import sys


def platform_name() -> str:
    if sys.platform == "darwin":
        return "macOS"
    if sys.platform == "win32":
        return "Windows"
    return sys.platform


def is_macos() -> bool:
    return sys.platform == "darwin"


def macos_screen_recording_hint() -> str:
    return (
        "macOS 需要允许屏幕录制权限：系统设置 -> 隐私与安全性 -> 屏幕录制，"
        "勾选 Teams Caption Translator，然后重启本程序。"
    )


def capture_failure_hint() -> str:
    if is_macos():
        return macos_screen_recording_hint()
    return "请确认字幕区域没有被遮挡，并重新点击“选择区域”。"


def ocr_empty_hint() -> str:
    if is_macos():
        return "如果截图里有字幕但 OCR 为空，先确认 Screen Recording 权限已开启；然后重启程序再试。"
    return "请打开调试截图确认里面是否有字幕；如果没有，请重新框选字幕区域。"
