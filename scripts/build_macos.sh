#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must be run on macOS." >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="$ROOT/.venv-macos"
SPEC="$ROOT/packaging/teams-caption-translator-macos.spec"
DIST_DIR="$ROOT/dist-macos"
BUILD_DIR="$ROOT/build-macos"
APP_PATH="$DIST_DIR/Teams Caption Translator.app"
APP_EXE="$APP_PATH/Contents/MacOS/Teams Caption Translator"
DMG_PATH="$ROOT/release/TeamsCaptionTranslator-v0.2.0-macos.dmg"
EASYOCR_MODEL_DIR="${TCT_EASYOCR_MODEL_DIR:-$HOME/.EasyOCR/model}"

"$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 10):
    raise SystemExit(
        "macOS packaging requires Python 3.10 or newer. "
        f"Current Python is {sys.version.split()[0]}."
    )

print(f"Using Python {sys.version.split()[0]} for macOS packaging.")
PY

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install --upgrade pyinstaller

mkdir -p "$EASYOCR_MODEL_DIR"
export TCT_EASYOCR_MODEL_DIR="$EASYOCR_MODEL_DIR"

python - <<'PY'
from pathlib import Path
import os

model_dir = Path(os.environ["TCT_EASYOCR_MODEL_DIR"]).expanduser()
model_dir.mkdir(parents=True, exist_ok=True)

try:
    import easyocr
except Exception as exc:
    raise SystemExit(f"EasyOCR import failed before macOS packaging: {exc}")

reader = easyocr.Reader(["ja"], gpu=False, model_storage_directory=str(model_dir))
required = ["craft_mlt_25k.pth", "japanese_g2.pth"]
missing = [name for name in required if not (model_dir / name).exists()]
if missing:
    raise SystemExit(f"EasyOCR model preparation failed. Missing: {', '.join(missing)} in {model_dir}")

print(f"EasyOCR models ready: {model_dir}")
PY

mkdir -p "$ROOT/release"
python -m PyInstaller --noconfirm --distpath "$DIST_DIR" --workpath "$BUILD_DIR" "$SPEC"

if [[ ! -d "$APP_PATH" ]]; then
  echo "Build failed: $APP_PATH was not created." >&2
  exit 1
fi

if [[ ! -x "$APP_EXE" ]]; then
  echo "Build failed: app executable was not found: $APP_EXE" >&2
  exit 1
fi

for model_name in craft_mlt_25k.pth japanese_g2.pth; do
  if ! find "$APP_PATH" -name "$model_name" -print -quit | grep -q .; then
    echo "Build failed: bundled EasyOCR model missing from app: $model_name" >&2
    exit 1
  fi
done

TCT_PLATFORM_DIAGNOSTIC_SMOKE=1 "$APP_EXE"
TCT_FIRST_RUN_SMOKE=1 "$APP_EXE"

rm -f "$DMG_PATH"
hdiutil create \
  -volname "Teams Caption Translator" \
  -srcfolder "$APP_PATH" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

echo "macOS app: $APP_PATH"
echo "macOS dmg: $DMG_PATH"
echo "Before release, run docs/MACOS_PACKAGING.md acceptance checks on a real Mac."
