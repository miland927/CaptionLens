from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from teams_caption_translator.dpi import enable_dpi_awareness

enable_dpi_awareness()

from teams_caption_translator.config import load_config
from teams_caption_translator.ui import TranslatorWindow


def main() -> int:
    config = load_config()
    app = TranslatorWindow(config)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
