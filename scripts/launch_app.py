from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import sys
import traceback


APP_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = APP_ROOT / "logs"
APP_LOG = LOG_DIR / "app.log"


def write_log(message: str) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    APP_LOG.write_text(f"[{timestamp}] {message}\n", encoding="utf-8")


def show_error(message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Teams 字幕翻译器启动失败", message)
        root.destroy()
    except Exception:
        return None


def main() -> int:
    sys.path.insert(0, str(APP_ROOT / "src"))
    try:
        if "--smoke" in sys.argv or os.environ.get("TCT_SMOKE") == "1":
            from teams_caption_translator.dpi import enable_dpi_awareness

            enable_dpi_awareness()
            from teams_caption_translator.config import AppConfig
            from teams_caption_translator.ui import TranslatorWindow

            app = TranslatorWindow(AppConfig())
            app.root.update()
            app.root.destroy()
            write_log("Smoke check OK")
            return 0

        from teams_caption_translator.main import main as app_main

        return app_main()
    except Exception:
        LOG_DIR.mkdir(exist_ok=True)
        traceback_text = traceback.format_exc()
        APP_LOG.write_text(traceback_text, encoding="utf-8")
        show_error(f"程序启动失败，错误日志已保存到:\n{APP_LOG}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
