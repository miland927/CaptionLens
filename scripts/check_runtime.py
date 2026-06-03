from __future__ import annotations

import importlib.util
import sys


REQUIRED_MODULES = {
    "PIL": "pillow",
    "mss": "mss",
    "deep_translator": "deep-translator",
    "easyocr": "easyocr",
    "tkinter": "tkinter",
}


def main() -> int:
    missing = []
    for module_name, package_name in REQUIRED_MODULES.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)

    if missing:
        print("Missing modules:", ", ".join(missing))
        return 1

    version = sys.version_info
    if (version.major, version.minor) < (3, 10):
        print(f"Python 3.10+ is required, got {sys.version.split()[0]}")
        return 1

    print("Runtime check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
