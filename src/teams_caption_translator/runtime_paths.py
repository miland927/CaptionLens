from __future__ import annotations

import os
from pathlib import Path
import sys


APP_NAME = "TeamsCaptionTranslator"


def app_base_dir() -> Path:
    if sys.platform == "win32":
        root = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if root:
            return Path(root) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"


def app_config_path() -> Path:
    return app_base_dir() / "config.json"


def app_log_dir() -> Path:
    return app_base_dir() / "logs"


def app_debug_dir() -> Path:
    return app_log_dir() / "debug"


def bundled_resource_dir() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root)
    return project_root()


def bundled_easyocr_model_dir() -> Path:
    return bundled_resource_dir() / "easyocr_model"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]
