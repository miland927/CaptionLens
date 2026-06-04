from __future__ import annotations

import io
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile


APP_NAME = "Teams 字幕翻译器"
APP_ID = "TeamsCaptionTranslator"
EXE_NAME = "TeamsCaptionTranslator.exe"
MARKER = b"TCT_PAYLOAD_V1"


def show_message(title: str, message: str, error: bool = False) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        if error:
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)
        root.destroy()
    except Exception:
        print(message, file=sys.stderr if error else sys.stdout)


def read_payload() -> bytes:
    exe_path = Path(sys.executable if getattr(sys, "frozen", False) else __file__)
    data = exe_path.read_bytes()
    if len(data) < len(MARKER) + 8:
        raise RuntimeError("安装包不完整：缺少 payload。")
    payload_size = struct.unpack("<Q", data[-8:])[0]
    marker_start = len(data) - 8 - len(MARKER)
    if data[marker_start : marker_start + len(MARKER)] != MARKER:
        raise RuntimeError("安装包不完整：payload 标记不存在。")
    payload_start = marker_start - payload_size
    if payload_start < 0:
        raise RuntimeError("安装包不完整：payload 大小异常。")
    return data[payload_start:marker_start]


def install_dir() -> Path:
    root = os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(root) / "Programs" / APP_ID


def start_menu_dir() -> Path:
    root = os.environ.get("APPDATA") or str(Path.home())
    return Path(root) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME


def desktop_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"


def create_shortcut(link_path: Path, target_path: Path) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    script = (
        "$w=New-Object -ComObject WScript.Shell;"
        f"$s=$w.CreateShortcut('{str(link_path).replace("'", "''")}');"
        f"$s.TargetPath='{str(target_path).replace("'", "''")}';"
        f"$s.WorkingDirectory='{str(target_path.parent).replace("'", "''")}';"
        "$s.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def write_uninstaller(target: Path) -> None:
    uninstall = target / "Uninstall.bat"
    uninstall.write_text(
        "@echo off\r\n"
        "setlocal\r\n"
        "echo Uninstalling Teams Caption Translator...\r\n"
        f'del /f /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{APP_NAME}\\{APP_NAME}.lnk" >nul 2>nul\r\n'
        f'rmdir "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{APP_NAME}" >nul 2>nul\r\n'
        f'del /f /q "%USERPROFILE%\\Desktop\\{APP_NAME}.lnk" >nul 2>nul\r\n'
        'cd /d "%TEMP%"\r\n'
        f'rmdir /s /q "{target}"\r\n',
        encoding="utf-8",
    )


def main() -> int:
    try:
        payload = read_payload()
        target = install_dir()
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            archive.extractall(target)

        app_exe = target / EXE_NAME
        if not app_exe.exists():
            raise RuntimeError(f"安装包不完整：未找到 {EXE_NAME}。")

        create_shortcut(desktop_dir() / f"{APP_NAME}.lnk", app_exe)
        create_shortcut(start_menu_dir() / f"{APP_NAME}.lnk", app_exe)
        write_uninstaller(target)

        show_message(APP_NAME, "安装完成。首次启动后请输入 DeepSeek API Key，然后选择字幕区域。")
        subprocess.Popen([str(app_exe)], cwd=str(target))
        return 0
    except Exception as exc:
        show_message(APP_NAME, f"安装失败：{exc}", error=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
