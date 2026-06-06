from __future__ import annotations

import os
import sys
from time import sleep
import traceback

from teams_caption_translator.runtime_paths import app_log_dir


def _widget_tree_text(widget) -> str:
    parts: list[str] = []
    try:
        value = widget.cget("text")
        if value:
            parts.append(str(value))
    except Exception:
        pass
    for child in widget.winfo_children():
        parts.append(_widget_tree_text(child))
    return "\n".join(part for part in parts if part)


def show_error(message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Teams 字幕翻译器", message)
        root.destroy()
    except Exception:
        print(message, file=sys.stderr)


def main() -> int:
    try:
        if os.environ.get("TCT_PLATFORM_DIAGNOSTIC_SMOKE") == "1":
            from teams_caption_translator.platform_diagnostics import (
                is_macos,
                macos_screen_recording_hint,
                platform_name,
            )
            from teams_caption_translator.runtime_paths import app_config_path

            log_dir = app_log_dir()
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "app.log"
            lines = [
                f"Platform diagnostic smoke: ok=True",
                f"platform={platform_name()}",
                f"config_path={app_config_path()}",
                f"log_dir={log_dir}",
            ]
            if is_macos():
                lines.append(f"macos_screen_recording_hint={macos_screen_recording_hint()}")
            log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return 0

        if os.environ.get("TCT_PREPARE_OCR_SMOKE") == "1":
            from teams_caption_translator.ocr import prepare_ocr_backend

            result = prepare_ocr_backend("ja", "auto")
            log_dir = app_log_dir()
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "app.log"
            log_path.write_text(
                f"OCR smoke: ok={result.ok}; engine={result.engine}; message={result.message}\n",
                encoding="utf-8",
            )
            return 0 if result.ok else 1

        if os.environ.get("TCT_DEEPSEEK_SMOKE") == "1":
            from teams_caption_translator.translator import create_translator

            api_key = os.environ.get("TCT_DEEPSEEK_API_KEY", "")
            translator = create_translator("deepseek", api_key)
            result = translator.translate("こんにちは。", "ja", "zh-CN", [])
            log_dir = app_log_dir()
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "app.log"
            log_path.write_text(
                f"DeepSeek smoke: ok=True; provider={result.provider}; translated_chars={len(result.text)}\n",
                encoding="utf-8",
            )
            return 0

        if os.environ.get("TCT_SMOKE") == "1":
            from teams_caption_translator.config import AppConfig
            from teams_caption_translator.dpi import enable_dpi_awareness
            from teams_caption_translator.ui import TranslatorWindow

            enable_dpi_awareness()
            app = TranslatorWindow(AppConfig())
            app.root.update()
            app.root.destroy()
            return 0

        if os.environ.get("TCT_FIRST_RUN_SMOKE") == "1":
            from teams_caption_translator.config import AppConfig
            from teams_caption_translator.dpi import enable_dpi_awareness
            from teams_caption_translator.ui import TranslatorWindow

            enable_dpi_awareness()
            app = TranslatorWindow(AppConfig())
            try:
                app.root.update()
                sleep(0.35)
                app.root.update()
                badge = str(app.status_badge.cget("text"))
                status = str(app.status.cget("text"))
                visible_text = _widget_tree_text(app.root)
                checks = {
                    "badge asks for key": badge == "输入 Key",
                    "status explains key flow": "粘贴 DeepSeek API Key" in status,
                    "guide shows full first-run flow": "粘贴 DeepSeek Key" in visible_text
                    and "测试 DeepSeek" in visible_text
                    and "准备 OCR" in visible_text
                    and "开始翻译" in visible_text,
                }
                failed = [name for name, ok in checks.items() if not ok]
                log_dir = app_log_dir()
                log_dir.mkdir(parents=True, exist_ok=True)
                log_path = log_dir / "app.log"
                if failed:
                    log_path.write_text(
                        f"First-run smoke failed: {failed}; badge={badge!r}; status={status!r}\n",
                        encoding="utf-8",
                    )
                    return 1
                log_path.write_text("First-run smoke: ok=True\n", encoding="utf-8")
                return 0
            finally:
                app.root.destroy()

        from teams_caption_translator.main import main as app_main

        return app_main()
    except Exception:
        log_dir = app_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "app.log"
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        show_error(f"程序启动失败，错误日志已保存到：\n{log_path}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
