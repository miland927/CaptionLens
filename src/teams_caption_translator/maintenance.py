from __future__ import annotations

from pathlib import Path
import shutil

from .runtime_paths import app_base_dir, app_debug_dir


def prune_debug_screenshots(max_files: int = 30, max_megabytes: int = 100) -> None:
    debug_dir = app_debug_dir()
    if not debug_dir.exists():
        return

    files = [path for path in debug_dir.glob("*.png") if path.is_file()]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)

    max_files = max(1, max_files)
    max_bytes = max(1, max_megabytes) * 1024 * 1024
    total = 0
    for index, path in enumerate(files):
        try:
            size = path.stat().st_size
        except OSError:
            continue
        total += size
        if index >= max_files or total > max_bytes:
            path.unlink(missing_ok=True)


def reset_app_data() -> Path:
    base_dir = app_base_dir()
    if base_dir.exists():
        shutil.rmtree(base_dir)
    return base_dir
