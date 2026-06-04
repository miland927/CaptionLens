from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

from .runtime_paths import app_config_path, project_root

APP_DIR = project_root()
LEGACY_CONFIG_PATH = APP_DIR / "config.json"
CONFIG_PATH = app_config_path()


@dataclass
class Region:
    x: int | None = None
    y: int | None = None
    w: int | None = None
    h: int | None = None

    @property
    def is_ready(self) -> bool:
        return all(v is not None for v in (self.x, self.y, self.w, self.h)) and self.w > 0 and self.h > 0


@dataclass
class AppConfig:
    region: Region = field(default_factory=Region)
    capture_fps: int = 10
    stable_frames: int = 3
    change_threshold: float = 3.5
    source_lang: str = "ja"
    target_lang: str = "zh-CN"
    ocr_lang: str = "ja"
    translator: str = "deepseek"
    window_opacity: float = 0.88
    window_always_top: bool = True
    auto_start: bool = False
    show_raw: bool = True
    deepseek_api_key: str = ""
    ocr_provider: str = "auto"
    max_translation_segments_per_batch: int = 2


def _merge_dict(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    default = asdict(AppConfig())
    source_path = path
    if not source_path.exists() and path == CONFIG_PATH and LEGACY_CONFIG_PATH.exists():
        source_path = LEGACY_CONFIG_PATH
    if not source_path.exists():
        return AppConfig()
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
        data = _merge_dict(default, raw)
        data["region"] = Region(**data.get("region", {}))
        config = AppConfig(**data)
        if source_path != path:
            save_config(config, path)
        return config
    except Exception:
        return AppConfig()


def save_config(config: AppConfig, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
