#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${VERSION:-0.2.0}"
DMG_PATH="$ROOT/release/TeamsCaptionTranslator-v${VERSION}-macos.dmg"
RELEASE_DIR="$ROOT/release/TeamsCaptionTranslator-v${VERSION}-macos"
ZIP_BASE="$ROOT/release/TeamsCaptionTranslator-v${VERSION}-macos"
ZIP_PATH="$ZIP_BASE.zip"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must be run on macOS after scripts/build_macos.sh." >&2
  exit 1
fi

if [[ ! -f "$DMG_PATH" ]]; then
  echo "Missing dmg: $DMG_PATH" >&2
  echo "Run: bash scripts/build_macos.sh" >&2
  exit 1
fi

bash "$ROOT/scripts/check_macos_release.sh" "$DMG_PATH"

rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

cp "$DMG_PATH" "$RELEASE_DIR/"
cp "$ROOT/docs/README_MACOS.txt" "$RELEASE_DIR/"
cp "$ROOT/docs/SEND_TO_MAC_TESTER.txt" "$RELEASE_DIR/"
cp "$ROOT/docs/MACOS_PACKAGING.md" "$RELEASE_DIR/"
cp "$ROOT/docs/MAC_TEST_RESULT_TEMPLATE.txt" "$RELEASE_DIR/"
cp "$ROOT/scripts/export_macos_support_bundle.sh" "$RELEASE_DIR/EXPORT_MACOS_SUPPORT_BUNDLE.sh"
chmod +x "$RELEASE_DIR/EXPORT_MACOS_SUPPORT_BUNDLE.sh"

HASH="$(shasum -a 256 "$DMG_PATH" | awk '{print toupper($1)}')"
SIZE="$(stat -f%z "$DMG_PATH")"

cat > "$RELEASE_DIR/SHA256.txt" <<EOF
Teams Caption Translator v${VERSION} macOS

File:
TeamsCaptionTranslator-v${VERSION}-macos.dmg

SHA256:
$HASH

Size:
$SIZE bytes
EOF

cat > "$RELEASE_DIR/RELEASE_MANIFEST.json" <<EOF
{
  "name": "Teams Caption Translator",
  "version": "${VERSION}",
  "package_platform": "macos",
  "recommended_zip": "TeamsCaptionTranslator-v${VERSION}-macos.zip",
  "dmg": {
    "file": "TeamsCaptionTranslator-v${VERSION}-macos.dmg",
    "sha256": "${HASH}",
    "size_bytes": ${SIZE}
  },
  "ordinary_user_python_required": false,
  "bundled_ocr_models": [
    "craft_mlt_25k.pth",
    "japanese_g2.pth"
  ],
  "config_location": "~/Library/Application Support/TeamsCaptionTranslator",
  "support_bundle": "EXPORT_MACOS_SUPPORT_BUNDLE.sh",
  "validation": {
    "build": "scripts/build_macos.sh completed on a real Mac",
    "release_check": "scripts/check_macos_release.sh passed on a real Mac",
    "screen_recording": "Screen Recording permission granted and screenshot capture verified",
    "real_teams": "real Teams rolling captions verified manually"
  },
  "macos_status": "built_on_real_mac_pending_manual_acceptance"
}
EOF

rm -f "$ZIP_PATH"
(
  cd "$ROOT/release"
  zip -qry "$(basename "$ZIP_PATH")" "$(basename "$RELEASE_DIR")"
)

echo "macOS release folder: $RELEASE_DIR"
echo "macOS release zip: $ZIP_PATH"
echo "DMG SHA256: $HASH"
