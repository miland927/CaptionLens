#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="${1:-$(pwd)}"
STAMP="$(date +%Y%m%d-%H%M%S)"
WORK_DIR="$OUTPUT_DIR/TeamsCaptionTranslatorSupport-$STAMP"
ZIP_PATH="$OUTPUT_DIR/TeamsCaptionTranslatorSupport-$STAMP.zip"
APP_ROOT="$HOME/Library/Application Support/TeamsCaptionTranslator"
LOG_DIR="$APP_ROOT/logs"
CONFIG_PATH="$APP_ROOT/config.json"

mkdir -p "$WORK_DIR"

{
  echo "{"
  echo "  \"generated_at\": \"$(date '+%Y-%m-%d %H:%M:%S')\","
  echo "  \"platform\": \"$(uname -s)\","
  echo "  \"platform_version\": \"$(sw_vers -productVersion 2>/dev/null || true)\","
  echo "  \"architecture\": \"$(uname -m)\","
  echo "  \"app_root_exists\": $(if [[ -d "$APP_ROOT" ]]; then echo true; else echo false; fi),"
  echo "  \"logs_exist\": $(if [[ -d "$LOG_DIR" ]]; then echo true; else echo false; fi),"
  echo "  \"config_exists\": $(if [[ -f "$CONFIG_PATH" ]]; then echo true; else echo false; fi)"
  echo "}"
} > "$WORK_DIR/system.json"

if [[ -d "$LOG_DIR" ]]; then
  cp -R "$LOG_DIR" "$WORK_DIR/logs" 2>/dev/null || {
    echo "Log directory existed, but could not be copied." > "$WORK_DIR/logs.copy_failed.txt"
  }
fi

if [[ -f "$CONFIG_PATH" ]]; then
  perl -pe 's/("(?:[^"\\]|\\.)*(?:api|key|token|secret|password)(?:[^"\\]|\\.)*"\s*:\s*)"(?:[^"\\]|\\.)*"/$1"***REDACTED***"/ig' \
    "$CONFIG_PATH" > "$WORK_DIR/config.redacted.json" 2>/dev/null || {
      echo "Config existed, but could not be redacted. Raw config was not copied." > "$WORK_DIR/config.redacted.txt"
      rm -f "$WORK_DIR/config.redacted.json"
    }
fi

cat > "$WORK_DIR/README.txt" <<'EOF'
This support bundle redacts fields matching api/key/token/secret/password.
Do not add your DeepSeek key manually.
EOF

rm -f "$ZIP_PATH"
(
  cd "$OUTPUT_DIR"
  zip -qry "$(basename "$ZIP_PATH")" "$(basename "$WORK_DIR")"
)
rm -rf "$WORK_DIR"

echo "Support bundle created:"
echo "$ZIP_PATH"
