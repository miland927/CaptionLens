from __future__ import annotations

from datetime import datetime
from pathlib import Path
from queue import Empty
from threading import Thread
from time import monotonic, sleep
import tkinter as tk
from tkinter import ttk

from .capture import create_capture_backend
from .config import AppConfig, Region, save_config
from .ocr import create_ocr_backend
from .pipeline import CaptionPipeline, PipelineEvent
from .text_utils import normalize_text


FONT_UI = "Microsoft YaHei UI"
FONT_MONO = "Consolas"

COLORS = {
    "bg": "#10131a",
    "panel": "#171c26",
    "panel_2": "#202735",
    "field": "#0b0f16",
    "line": "#303848",
    "text": "#f3f7fb",
    "muted": "#8e9aaa",
    "soft": "#c7d0df",
    "accent": "#4dd0e1",
    "accent_2": "#ff4d6d",
    "warn": "#ffd166",
    "ok": "#5ee6a8",
    "danger": "#ff6b6b",
}

APP_ROOT = Path(__file__).resolve().parents[2]
DEBUG_DIR = APP_ROOT / "logs" / "debug"


class RegionSelector:
    def __init__(self) -> None:
        self.selected: Region | None = None
        self._start_x = 0
        self._start_y = 0
        self._rect = None

    def select(self) -> Region | None:
        root = tk.Toplevel()
        root.attributes("-fullscreen", True)
        root.attributes("-alpha", 0.36)
        root.attributes("-topmost", True)
        root.configure(bg="#05070a")

        canvas = tk.Canvas(root, cursor="cross", bg="#05070a", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        width = root.winfo_screenwidth()
        canvas.create_text(
            width // 2,
            42,
            text="拖动鼠标框选 Teams 字幕区域，松开确认",
            fill="#ffffff",
            font=(FONT_UI, 18, "bold"),
        )
        canvas.create_text(width // 2, 78, text="按 Esc 取消", fill="#d4d9e2", font=(FONT_UI, 11))

        def on_press(event) -> None:
            self._start_x, self._start_y = event.x, event.y
            if self._rect:
                canvas.delete(self._rect)
            self._rect = canvas.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline=COLORS["accent_2"],
                width=3,
                fill=COLORS["accent_2"],
                stipple="gray25",
            )

        def on_drag(event) -> None:
            if self._rect:
                canvas.coords(self._rect, self._start_x, self._start_y, event.x, event.y)

        def on_release(event) -> None:
            x1, y1 = min(self._start_x, event.x), min(self._start_y, event.y)
            x2, y2 = max(self._start_x, event.x), max(self._start_y, event.y)
            if x2 - x1 >= 20 and y2 - y1 >= 20:
                self.selected = Region(x=x1, y=y1, w=x2 - x1, h=y2 - y1)
                root.destroy()

        def on_escape(_event) -> None:
            self.selected = None
            root.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        root.bind("<Escape>", on_escape)
        root.grab_set()
        root.wait_window()
        return self.selected


class TranslatorWindow:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.pipeline: CaptionPipeline | None = None
        self.history: list[tuple[str, str]] = []
        self.history_visible = False
        self._status_hold_until = 0.0

        self.root = tk.Tk()
        self.root.title("Teams 字幕翻译器")
        self.root.geometry("720x500+60+60")
        self.root.minsize(560, 390)
        self.root.attributes("-topmost", self.config.window_always_top)
        self.root.attributes("-alpha", self.config.window_opacity)
        self.root.configure(bg=COLORS["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.show_raw_var = tk.BooleanVar(master=self.root, value=self.config.show_raw)
        self.topmost_var = tk.BooleanVar(master=self.root, value=self.config.window_always_top)
        self.opacity_var = tk.DoubleVar(master=self.root, value=self.config.window_opacity)
        self.deepseek_key_var = tk.StringVar(master=self.root, value=self.config.deepseek_api_key)
        self.translator_var = tk.StringVar(master=self.root, value=self.config.translator)
        self.source_lang_var = tk.StringVar(master=self.root, value=self.config.source_lang)
        self.target_lang_var = tk.StringVar(master=self.root, value=self.config.target_lang)
        self.ocr_lang_var = tk.StringVar(master=self.root, value=self.config.ocr_lang)
        self.ocr_provider_var = tk.StringVar(master=self.root, value=self.config.ocr_provider)

        self._build()
        self._refresh_region()
        if self.config.auto_start and self.config.region.is_ready:
            self.root.after(400, self.start)

    def _build(self) -> None:
        self._configure_style()

        shell = tk.Frame(self.root, bg=COLORS["bg"])
        shell.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)

        header = tk.Frame(shell, bg=COLORS["bg"])
        header.pack(fill=tk.X, pady=(0, 10))

        title_block = tk.Frame(header, bg=COLORS["bg"])
        title_block.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(
            title_block,
            text="Teams 字幕翻译器",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=(FONT_UI, 18, "bold"),
        ).pack(anchor=tk.W)
        tk.Label(
            title_block,
            text="框选字幕区域后自动识别并翻译",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=(FONT_UI, 9),
        ).pack(anchor=tk.W, pady=(2, 0))

        self.status_badge = tk.Label(
            header,
            text="待机",
            bg=COLORS["panel_2"],
            fg=COLORS["soft"],
            font=(FONT_UI, 10, "bold"),
            padx=12,
            pady=6,
        )
        self.status_badge.pack(side=tk.RIGHT, padx=(8, 0))

        controls = tk.Frame(shell, bg=COLORS["panel"], highlightbackground=COLORS["line"], highlightthickness=1)
        controls.pack(fill=tk.X, pady=(0, 10))
        controls.columnconfigure(5, weight=1)

        self.start_btn = self._button(controls, "开始翻译", self.toggle, COLORS["accent_2"], "#ffffff")
        self.start_btn.grid(row=0, column=0, padx=(10, 6), pady=10, sticky="w")
        self.select_btn = self._button(controls, "选择区域", self.select_region, COLORS["panel_2"], COLORS["text"])
        self.select_btn.grid(row=0, column=1, padx=6, pady=10, sticky="w")
        self.auto_region_btn = self._button(controls, "推荐字幕区", self.use_recommended_region, "#263142", COLORS["soft"])
        self.auto_region_btn.grid(row=0, column=2, padx=6, pady=10, sticky="w")
        self.test_btn = self._button(controls, "测试OCR", self.test_ocr_once, "#263142", COLORS["soft"])
        self.test_btn.grid(row=0, column=3, padx=6, pady=10, sticky="w")
        self.clear_btn = self._button(controls, "清空", self.clear, "#263142", COLORS["soft"])
        self.clear_btn.grid(row=0, column=4, padx=6, pady=10, sticky="w")

        self.region_label = tk.Label(
            controls,
            text="",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            anchor="e",
            font=(FONT_MONO, 9),
        )
        self.region_label.grid(row=0, column=5, padx=(8, 10), pady=10, sticky="ew")

        settings = tk.Frame(shell, bg=COLORS["bg"])
        settings.pack(fill=tk.X, pady=(0, 10))
        self.raw_check = self._check(settings, "显示原文", self.show_raw_var, self._toggle_raw)
        self.raw_check.pack(side=tk.LEFT)
        self.top_check = self._check(settings, "窗口置顶", self.topmost_var, self._toggle_topmost)
        self.top_check.pack(side=tk.LEFT, padx=(12, 0))
        tk.Label(settings, text="透明度", bg=COLORS["bg"], fg=COLORS["muted"], font=(FONT_UI, 9)).pack(side=tk.LEFT, padx=(18, 6))
        opacity = ttk.Scale(settings, from_=0.55, to=1.0, variable=self.opacity_var, command=self._set_opacity)
        opacity.pack(side=tk.LEFT, fill=tk.X, expand=True)

        api_settings = tk.Frame(shell, bg=COLORS["panel"], highlightbackground=COLORS["line"], highlightthickness=1)
        api_settings.pack(fill=tk.X, pady=(0, 8))
        tk.Label(api_settings, text="DeepSeek Key", bg=COLORS["panel"], fg=COLORS["soft"], font=(FONT_UI, 9, "bold")).pack(
            side=tk.LEFT, padx=(10, 6), pady=8
        )
        self.key_entry = tk.Entry(
            api_settings,
            textvariable=self.deepseek_key_var,
            show="*",
            bg=COLORS["field"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief=tk.FLAT,
            font=(FONT_MONO, 10),
        )
        self.key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=8)
        self.save_settings_btn = self._button(api_settings, "保存设置", self.save_settings, "#263142", COLORS["soft"])
        self.save_settings_btn.pack(side=tk.LEFT, padx=(0, 10), pady=8)

        advanced = tk.Frame(shell, bg=COLORS["bg"])
        advanced.pack(fill=tk.X, pady=(0, 8))
        self._combo(advanced, "翻译", self.translator_var, ("deepseek", "google", "echo"), self.save_settings).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        self._combo(advanced, "原文", self.source_lang_var, ("ja", "en", "ko", "auto"), self.save_settings).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        self._combo(advanced, "译文", self.target_lang_var, ("zh-CN", "zh-TW", "en", "ja"), self.save_settings).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        self._combo(advanced, "OCR语言", self.ocr_lang_var, ("ja", "en", "ko", "zh-CN"), self.save_settings).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        self._combo(advanced, "OCR引擎", self.ocr_provider_var, ("auto", "windows", "easyocr", "rapidocr"), self.save_settings).pack(
            side=tk.LEFT
        )

        self.status = tk.Label(shell, text="", bg=COLORS["bg"], fg=COLORS["muted"], anchor="w", font=(FONT_UI, 9))
        self.status.pack(fill=tk.X, pady=(0, 8))

        self.guide_frame = tk.Frame(shell, bg=COLORS["panel_2"], highlightbackground=COLORS["line"], highlightthickness=1)
        self.guide_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(
            self.guide_frame,
            text="首次使用",
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            font=(FONT_UI, 10, "bold"),
        ).pack(anchor=tk.W, padx=10, pady=(8, 2))
        tk.Label(
            self.guide_frame,
            text="1. 打开 Teams 字幕    2. 点“选择区域”框住字幕    3. 点“开始翻译”",
            bg=COLORS["panel_2"],
            fg=COLORS["soft"],
            font=(FONT_UI, 10),
        ).pack(anchor=tk.W, padx=10, pady=(0, 8))

        self.raw_frame, self.raw_text = self._text_panel(shell, "日语原文", COLORS["warn"], 3, False)
        self.trans_frame, self.trans_text = self._text_panel(shell, "中文翻译", COLORS["accent"], 6, True)

        footer = tk.Frame(shell, bg=COLORS["bg"])
        footer.pack(fill=tk.X)
        self.metrics = tk.Label(footer, text="延迟: -", bg=COLORS["bg"], fg=COLORS["muted"], anchor="w", font=(FONT_MONO, 9))
        self.metrics.pack(side=tk.LEFT)
        self.history_btn = self._link_button(footer, "显示历史", self.toggle_history)
        self.history_btn.pack(side=tk.RIGHT)

        self.history_frame = tk.Frame(shell, bg=COLORS["panel"], highlightbackground=COLORS["line"], highlightthickness=1)
        self.history_text = tk.Text(
            self.history_frame,
            height=5,
            bg=COLORS["field"],
            fg=COLORS["soft"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            font=(FONT_UI, 9),
        )
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.history_text.configure(state=tk.DISABLED)
        self._toggle_raw()

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Horizontal.TScale",
            background=COLORS["bg"],
            troughcolor=COLORS["panel_2"],
            bordercolor=COLORS["bg"],
            lightcolor=COLORS["bg"],
            darkcolor=COLORS["bg"],
        )

    def _button(self, parent: tk.Widget, text: str, command, bg: str, fg: str) -> tk.Button:
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=COLORS["accent"],
            activeforeground="#061016",
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            font=(FONT_UI, 10, "bold"),
        )
        return button

    def _link_button(self, parent: tk.Widget, text: str, command) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=COLORS["bg"],
            fg=COLORS["accent"],
            activebackground=COLORS["bg"],
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            padx=0,
            cursor="hand2",
            font=(FONT_UI, 9, "bold"),
        )

    def _check(self, parent: tk.Widget, text: str, variable: tk.BooleanVar, command) -> tk.Checkbutton:
        return tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            command=command,
            bg=COLORS["bg"],
            fg=COLORS["soft"],
            activebackground=COLORS["bg"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["panel_2"],
            font=(FONT_UI, 9),
        )

    def _combo(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        values: tuple[str, ...],
        command,
    ) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["bg"])
        tk.Label(frame, text=label, bg=COLORS["bg"], fg=COLORS["muted"], font=(FONT_UI, 9)).pack(side=tk.LEFT, padx=(0, 4))
        combo = ttk.Combobox(frame, textvariable=variable, values=values, state="readonly", width=max(7, len(label) + 2))
        combo.pack(side=tk.LEFT)
        combo.bind("<<ComboboxSelected>>", lambda _event: command())
        return frame

    def _text_panel(self, parent: tk.Widget, title: str, fg: str, height: int, bold: bool) -> tuple[tk.Frame, tk.Text]:
        frame = tk.Frame(parent, bg=COLORS["panel"], highlightbackground=COLORS["line"], highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        top = tk.Frame(frame, bg=COLORS["panel"])
        top.pack(fill=tk.X, padx=10, pady=(8, 3))
        tk.Label(top, text=title, bg=COLORS["panel"], fg=COLORS["soft"], font=(FONT_UI, 9, "bold")).pack(side=tk.LEFT)
        text = tk.Text(
            frame,
            height=height,
            bg=COLORS["field"],
            fg=fg,
            insertbackground=fg,
            relief=tk.FLAT,
            wrap=tk.WORD,
            font=(FONT_UI, 15, "bold" if bold else "normal"),
            spacing1=2,
            spacing3=2,
            padx=10,
            pady=8,
        )
        text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        text.configure(state=tk.DISABLED)
        return frame, text

    def select_region(self) -> None:
        self._set_status("选择中", "请在屏幕上框选字幕区域...", COLORS["warn"])
        selected = RegionSelector().select()
        if selected:
            self.config.region = selected
            save_config(self.config)
            self._refresh_region()
            self._set_status("已就绪", "区域已保存，可以开始翻译。", COLORS["ok"])
        else:
            self._set_status("待机", "未选择区域。", COLORS["soft"])

    def use_recommended_region(self) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = int(screen_w * 0.62)
        height = int(screen_h * 0.18)
        x = int((screen_w - width) / 2)
        y = int(screen_h * 0.78)
        self.config.region = Region(x=x, y=y, w=width, h=height)
        save_config(self.config)
        self._refresh_region()
        self._set_status("已设置", "已使用屏幕底部推荐字幕区，请先点击“测试OCR”。", COLORS["ok"])

    def test_ocr_once(self) -> None:
        if not self.config.region.is_ready:
            self._set_status("待选区", "请先选择字幕区域，再测试 OCR。", COLORS["warn"])
            return
        self.test_btn.configure(state=tk.DISABLED)
        self._set_status("测试中", "正在临时隐藏窗口并测试当前选区 OCR...", COLORS["warn"])
        Thread(target=self._test_ocr_worker, daemon=True).start()

    def _test_ocr_worker(self) -> None:
        try:
            self.root.after(0, self.root.withdraw)
            sleep(0.35)
            capture = create_capture_backend()
            try:
                frame = capture.grab(self.config.region)
            finally:
                capture.close()
            DEBUG_DIR.mkdir(parents=True, exist_ok=True)
            debug_path = DEBUG_DIR / f"ocr_region_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            frame.image.save(debug_path)
            ocr = create_ocr_backend(self.config.ocr_lang, self.config.ocr_provider)
            text = normalize_text(ocr.recognize(frame.image))
            if text:
                self.root.after(0, lambda: self._finish_ocr_test(text, f"OCR 测试成功：{ocr.name}；截图：{debug_path}", True))
            else:
                self.root.after(
                    0,
                    lambda: self._finish_ocr_test(
                        "",
                        f"OCR 没识别到文字。请打开截图确认里面是否有字幕：{debug_path}",
                        False,
                    ),
                )
        except Exception as exc:
            self.root.after(0, lambda: self._finish_ocr_test("", f"OCR 测试失败：{exc}", False))

    def _finish_ocr_test(self, text: str, message: str, ok: bool) -> None:
        self.root.deiconify()
        self.root.lift()
        self.test_btn.configure(state=tk.NORMAL)
        if text:
            self._set_text(self.raw_text, text)
            self._set_text(self.trans_text, "测试只做 OCR，不调用翻译。识别到原文后再点“开始翻译”。")
        self._set_status("测试完成" if ok else "未识别", message, COLORS["ok"] if ok else COLORS["warn"])

    def toggle(self) -> None:
        if self.pipeline:
            self.stop()
        else:
            self.start()

    def start(self) -> None:
        self.save_settings(silent=True)
        if not self.config.region.is_ready:
            self._set_status("待选区", "请先选择 Teams 字幕区域。", COLORS["warn"])
            return
        if self.config.translator == "deepseek" and not self.config.deepseek_api_key.strip():
            self._set_status("缺少 Key", "请先输入 DeepSeek API Key，然后点“保存设置”。", COLORS["warn"])
            self.key_entry.focus_set()
            return
        self._move_window_away_from_region()
        self.pipeline = CaptionPipeline(self.config)
        self.pipeline.start()
        self.start_btn.configure(text="停止翻译", bg=COLORS["danger"])
        self.select_btn.configure(state=tk.DISABLED)
        self._set_status("运行中", "正在捕获字幕区域...", COLORS["ok"])
        self.root.after(80, self._poll_events)

    def _move_window_away_from_region(self) -> None:
        r = self.config.region
        if not r.is_ready:
            return
        self.root.update_idletasks()
        wx, wy = self.root.winfo_x(), self.root.winfo_y()
        ww, wh = self.root.winfo_width(), self.root.winfo_height()
        rx, ry, rw, rh = r.x, r.y, r.w, r.h
        overlaps = wx < rx + rw and wx + ww > rx and wy < ry + rh and wy + wh > ry
        if not overlaps:
            return

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        margin = 18
        candidates = [
            (max(margin, rx - ww - margin), wy),
            (min(screen_w - ww - margin, rx + rw + margin), wy),
            (wx, max(margin, ry - wh - margin)),
            (wx, min(screen_h - wh - margin, ry + rh + margin)),
            (margin, margin),
        ]
        for nx, ny in candidates:
            nx = max(margin, min(nx, screen_w - ww - margin))
            ny = max(margin, min(ny, screen_h - wh - margin))
            if not (nx < rx + rw and nx + ww > rx and ny < ry + rh and ny + wh > ry):
                self.root.geometry(f"+{int(nx)}+{int(ny)}")
                self._set_status("已避让", "窗口与字幕区域重叠，已自动挪开。", COLORS["ok"])
                return

    def stop(self) -> None:
        if self.pipeline:
            self.pipeline.stop()
            self.pipeline = None
        self.start_btn.configure(text="开始翻译", bg=COLORS["accent_2"])
        self.select_btn.configure(state=tk.NORMAL)
        self._set_status("已停止", "翻译已暂停。", COLORS["soft"])

    def _poll_events(self) -> None:
        if not self.pipeline:
            return
        try:
            while True:
                self._handle_event(self.pipeline.events.get_nowait())
        except Empty:
            pass
        self.root.after(80, self._poll_events)

    def _handle_event(self, event: PipelineEvent) -> None:
        if event.kind == "result":
            self.guide_frame.pack_forget()
            self._set_text(self.raw_text, event.raw_text)
            self._set_text(self.trans_text, event.translated_text)
            self._set_status("已翻译", event.detail, COLORS["ok"])
            self.metrics.configure(
                text=f"OCR {event.ocr_ms:.0f} ms | 翻译 {event.translation_ms:.0f} ms | 总计 {event.total_ms:.0f} ms"
            )
            self.history.append((event.raw_text, event.translated_text))
            if len(self.history) > 80:
                self.history.pop(0)
            if self.history_visible:
                self._refresh_history()
        elif event.kind == "empty":
            self._status_hold_until = monotonic() + 3.5
            self._set_status("等待字幕", event.detail or "等待字幕文字出现...", COLORS["warn"])
            self.metrics.configure(text=f"OCR {event.ocr_ms:.0f} ms | 未识别到文字")
        elif event.kind == "capture":
            if monotonic() < self._status_hold_until:
                return
            self._set_status("截图中", event.detail, COLORS["soft"])
        elif event.kind == "loading":
            self._set_status("加载中", event.detail, COLORS["warn"])
        elif event.kind == "error":
            self._status_hold_until = monotonic() + 6.0
            self._set_status("错误", event.detail, COLORS["danger"])

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.configure(state=tk.DISABLED)

    def _set_status(self, badge: str, detail: str, color: str) -> None:
        self.status_badge.configure(text=badge, fg=color)
        self.status.configure(text=detail)

    def _refresh_region(self) -> None:
        r = self.config.region
        if r.is_ready:
            self.region_label.configure(text=f"x={r.x}  y={r.y}  w={r.w}  h={r.h}")
            self._set_status("已就绪", "区域已配置，点击“开始翻译”即可使用。", COLORS["ok"])
        else:
            self.region_label.configure(text="未选择区域")
            self._set_status("待机", "请先点击“选择区域”，框住 Teams 字幕出现的位置。", COLORS["soft"])

    def _toggle_raw(self) -> None:
        self.config.show_raw = self.show_raw_var.get()
        if self.config.show_raw:
            self.raw_frame.pack(fill=tk.BOTH, expand=True, before=self.trans_frame, pady=(0, 10))
        else:
            self.raw_frame.pack_forget()
        save_config(self.config)

    def _toggle_topmost(self) -> None:
        self.config.window_always_top = self.topmost_var.get()
        self.root.attributes("-topmost", self.config.window_always_top)
        save_config(self.config)

    def _set_opacity(self, _value: str) -> None:
        self.config.window_opacity = round(float(self.opacity_var.get()), 2)
        self.root.attributes("-alpha", self.config.window_opacity)
        save_config(self.config)

    def save_settings(self, silent: bool = False) -> None:
        self.config.deepseek_api_key = self.deepseek_key_var.get().strip()
        self.config.translator = self.translator_var.get()
        self.config.source_lang = self.source_lang_var.get()
        self.config.target_lang = self.target_lang_var.get()
        self.config.ocr_lang = self.ocr_lang_var.get()
        self.config.ocr_provider = self.ocr_provider_var.get()
        save_config(self.config)
        if not silent:
            self._set_status("已保存", "翻译、语言和 OCR 设置已保存。", COLORS["ok"])

    def toggle_history(self) -> None:
        self.history_visible = not self.history_visible
        if self.history_visible:
            self.history_btn.configure(text="隐藏历史")
            self.history_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 0))
            self._refresh_history()
        else:
            self.history_btn.configure(text="显示历史")
            self.history_frame.pack_forget()

    def _refresh_history(self) -> None:
        self.history_text.configure(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)
        for index, (raw, translated) in enumerate(self.history[-20:], 1):
            self.history_text.insert(tk.END, f"{index}. {raw}\n   {translated}\n\n")
        self.history_text.configure(state=tk.DISABLED)

    def clear(self) -> None:
        self.history.clear()
        self._set_text(self.raw_text, "")
        self._set_text(self.trans_text, "")
        self.metrics.configure(text="延迟: -")
        if self.history_visible:
            self._refresh_history()

    def close(self) -> None:
        self.stop()
        save_config(self.config)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
