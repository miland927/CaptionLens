#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DMG_PATH="${1:-$ROOT/release/TeamsCaptionTranslator-v0.2.0-macos.dmg}"
APP_PATH="$ROOT/dist-macos/Teams Caption Translator.app"
APP_EXE="$APP_PATH/Contents/MacOS/Teams Caption Translator"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must be run on macOS." >&2
  exit 1
fi

if [[ ! -f "$DMG_PATH" ]]; then
  echo "Missing dmg: $DMG_PATH" >&2
  exit 1
fi

if [[ ! -x "$APP_EXE" ]]; then
  echo "Missing app executable: $APP_EXE" >&2
  exit 1
fi

for model_name in craft_mlt_25k.pth japanese_g2.pth; do
  if ! find "$APP_PATH" -name "$model_name" -print -quit | grep -q .; then
    echo "Missing bundled EasyOCR model in app: $model_name" >&2
    exit 1
  fi
done

TCT_PLATFORM_DIAGNOSTIC_SMOKE=1 "$APP_EXE"
TCT_FIRST_RUN_SMOKE=1 "$APP_EXE"

APP_SUPPORT="$HOME/Library/Application Support/TeamsCaptionTranslator"
APP_LOG="$APP_SUPPORT/logs/app.log"

if [[ ! -f "$APP_LOG" ]]; then
  echo "Missing app log after smoke: $APP_LOG" >&2
  exit 1
fi

if ! grep -q "platform=macOS" "$APP_LOG"; then
  echo "Platform diagnostic did not report macOS." >&2
  exit 1
fi

hdiutil verify "$DMG_PATH"

echo "macOS release smoke passed."
echo "Next manual check: grant Screen Recording permission, open Teams captions, select region, Test OCR, then Start Translation."
