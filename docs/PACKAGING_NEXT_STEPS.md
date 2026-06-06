# Packaging Next Steps

## Current Answer

Windows support is implemented for ordinary users:

- The recommended Windows release zip is `release\TeamsCaptionTranslator-v0.2.0-windows.zip`.
- `release\TeamsCaptionTranslator-v0.2.0.zip` is kept as a compatibility copy for older instructions.
- The installer inside it is `TeamsCaptionTranslatorSetup-0.2.0.exe`.
- The Windows installer bundles the frozen Python runtime, application code, and EasyOCR Japanese models.
- A Windows user does not need to install Python.

macOS support is not implemented yet:

- macOS packaging scaffolding exists, but no verified `.app` or `.dmg` artifact has been produced on a real Mac yet.
- The current installer technology is Inno Setup, which is Windows-only.
- macOS still needs separate packaging, permission handling, and real-device verification.

Use `docs/FINAL_ACCEPTANCE_MATRIX.md` as the source of truth for what counts as complete. The full goal is not done until both Windows and macOS rows have real evidence.

## Next Work To Reach The Full Goal

### 1. Finish Windows Release Confidence

Required evidence before calling Windows fully done:

- Run `release\TeamsCaptionTranslator-v0.2.0\CLEAN_MACHINE_CHECK.ps1` on a clean Windows machine, VM, or Windows Sandbox.
- Run the same script with a real DeepSeek key so the DeepSeek smoke test is not skipped.
- Run `MANUAL_TEAMS_CHECK.md` against a real Teams rolling-caption session.
- Confirm that old translated lines remain, new lines append as `speaker: content`, and the UI remains readable.

### 2. Add macOS Packaging Support

Implementation items already staged:

- `packaging\teams-caption-translator-macos.spec` defines a PyInstaller `.app` bundle.
- `scripts\build_macos.sh` builds `Teams Caption Translator.app` and `TeamsCaptionTranslator-v0.2.0-macos.dmg` on macOS.
- `scripts\build_macos.sh` now runs platform and first-run UI smoke checks on the generated `.app`.
- `scripts\check_macos_release.sh` verifies the generated `.dmg` and basic app startup on a real Mac.
- Config and logs now use `~/Library/Application Support/TeamsCaptionTranslator` on macOS.
- `docs\MACOS_PACKAGING.md` records macOS build steps and acceptance checks.
- `docs\FINAL_ACCEPTANCE_MATRIX.md` records the final Windows/macOS completion standard.

Remaining implementation or validation items:

- Build the `.app` and `.dmg` on a real Mac.
- Confirm that the bundled EasyOCR model files are included in the macOS app.
- Use EasyOCR as the effective default OCR route on macOS.
- Add or verify first-run UI copy for Screen Recording permission if screenshot capture fails.
- Verify screenshot capture, overlay/topmost behavior, OCR preparation, DeepSeek translation, and rolling transcript display on a real Mac.
- Prepare and verify `release\TeamsCaptionTranslator-v0.2.0-macos.zip` on a real Mac.

### 3. Release Naming

Recommended naming once both platforms exist:

- `TeamsCaptionTranslator-v0.2.0-windows.zip`
- `TeamsCaptionTranslator-v0.2.0-macos.dmg`

Until then, the current release should be described as Windows-only.
