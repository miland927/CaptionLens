from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REQUIRED_MODULES = {
    "PIL": "pillow",
    "mss": "mss",
    "deep_translator": "deep-translator",
    "easyocr": "easyocr",
    "tkinter": "tkinter",
}

APP_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = APP_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from teams_caption_translator.runtime_paths import app_config_path

CONFIG_PATH = app_config_path()
LEGACY_CONFIG_PATH = APP_ROOT / "config.json"


def has_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def load_config() -> dict:
    source_path = CONFIG_PATH if CONFIG_PATH.exists() else LEGACY_CONFIG_PATH
    if not source_path.exists():
        return {}
    try:
        return json.loads(source_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def check_windows_ocr(language: str = "ja-JP") -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "Windows OCR 仅在 Windows 上可用"
    script = rf"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Foundation, ContentType=WindowsRuntime]
$lang = [Windows.Globalization.Language]::new("{language}")
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
if ($engine) {{ "OK" }} else {{ "MISSING" }}
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True,
            text=True,
            timeout=6,
        )
    except Exception as exc:
        return False, f"Windows OCR 检测失败: {exc}"
    if result.returncode == 0 and "OK" in result.stdout:
        return True, f"Windows OCR 可用: {language}"
    return False, f"Windows OCR 不可用: {language}。可继续使用 EasyOCR。"


def test_deepseek(api_key: str) -> tuple[bool, str]:
    api_key = api_key.strip()
    if not api_key:
        return False, "config.json 里没有 deepseek_api_key"
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "只回答 OK"},
            {"role": "user", "content": "ping"},
        ],
        "max_tokens": 8,
        "temperature": 0,
    }
    request = Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return False, f"DeepSeek API 错误 {exc.code}: {body[:180]}"
    except URLError as exc:
        return False, f"DeepSeek 网络连接失败: {exc.reason}"
    except Exception as exc:
        return False, f"DeepSeek 测试失败: {exc}"
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    return bool(content), "DeepSeek API 可用" if content else "DeepSeek 返回为空"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deepseek", action="store_true", help="测试 config.json 中的 DeepSeek API Key")
    parser.add_argument("--windows-ocr", action="store_true", help="只检测 Windows OCR")
    args = parser.parse_args()

    version = sys.version_info
    if (version.major, version.minor) < (3, 10):
        print(f"Python 3.10+ is required, got {sys.version.split()[0]}")
        return 1

    config = load_config()
    ocr_lang = config.get("ocr_lang", "ja")
    windows_lang = "ja-JP" if str(ocr_lang).lower().startswith("ja") else str(ocr_lang)

    if args.windows_ocr:
        ok, message = check_windows_ocr(windows_lang)
        print(message)
        return 0 if ok else 1

    if args.deepseek:
        ok, message = test_deepseek(str(config.get("deepseek_api_key", "")))
        print(message)
        return 0 if ok else 1

    missing = []
    for module_name, package_name in REQUIRED_MODULES.items():
        if not has_module(module_name):
            missing.append(package_name)

    if missing:
        print("Missing modules:", ", ".join(missing))
        return 1

    print(f"Runtime check OK: Python {sys.version.split()[0]}")
    ok, message = check_windows_ocr(windows_lang)
    print(message)
    if has_module("easyocr"):
        print("EasyOCR 模块可用")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
