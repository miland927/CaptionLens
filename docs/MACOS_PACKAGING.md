# macOS Packaging

This project can only produce a trustworthy macOS package on a real Mac.

The Windows machine can keep the source ready, but it cannot verify macOS screen capture permission, Tk window behavior, EasyOCR runtime loading, or the final `.dmg`.

## Build On macOS

If the source is being prepared from Windows, first create a clean source package:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\prepare_macos_source_package.ps1
```

Send `release\TeamsCaptionTranslator-v0.2.0-macos-source.zip` to the Mac builder. It excludes local virtual environments, build outputs, logs, release artifacts, and `config.json`.

The script also writes `release\TeamsCaptionTranslator-v0.2.0-macos-source.SOURCE_PACKAGE_MANIFEST.json` and includes `SOURCE_PACKAGE_MANIFEST.json` inside the zip. Use it to confirm the source package hash, excluded local files, and the exact Mac build commands.

Requirements:

- macOS 13 or newer is recommended.
- Python 3.10 or newer.
- Internet access for the first dependency install.
- Internet access for the first EasyOCR model preparation, unless the model files already exist in `~/.EasyOCR/model`.

`scripts/build_macos.sh` checks the selected Python version before creating `.venv-macos` and fails early if it is older than Python 3.10.

Build:

```bash
cd "/path/to/Dmsch v0.2"
bash scripts/build_macos.sh
```

The build script also runs two smoke checks on the generated app:

- `TCT_PLATFORM_DIAGNOSTIC_SMOKE=1`
- `TCT_FIRST_RUN_SMOKE=1`

Before PyInstaller runs, the build script initializes EasyOCR for Japanese and verifies these model files:

- `craft_mlt_25k.pth`
- `japanese_g2.pth`

After PyInstaller finishes, the build script also searches the generated `.app` and fails if either model is missing.

Expected outputs:

```text
dist-macos/Teams Caption Translator.app
release/TeamsCaptionTranslator-v0.2.0-macos.dmg
```

After build, run:

```bash
bash scripts/check_macos_release.sh
```

This verifies that the app executable exists, the platform diagnostic writes macOS app-support logs, the first-run UI can open, and the `.dmg` passes `hdiutil verify`.

It also verifies that the generated `.app` contains the bundled EasyOCR detection and Japanese recognition models.

To prepare the final macOS release folder and zip after those checks pass, run:

```bash
bash scripts/prepare_macos_release.sh
```

Expected release outputs:

```text
release/TeamsCaptionTranslator-v0.2.0-macos
release/TeamsCaptionTranslator-v0.2.0-macos.zip
```

The release folder includes the `.dmg`, `README_MACOS.txt`, `SEND_TO_MAC_TESTER.txt`, `MACOS_PACKAGING.md`, `MAC_TEST_RESULT_TEMPLATE.txt`, `EXPORT_MACOS_SUPPORT_BUNDLE.sh`, `RELEASE_MANIFEST.json`, and `SHA256.txt`.

## First-Run Permission

macOS normally requires Screen Recording permission before desktop screenshots work.

After launching the app:

1. Open System Settings.
2. Go to Privacy & Security.
3. Go to Screen Recording.
4. Enable permission for `Teams Caption Translator`.
5. Quit and reopen the app.

Without this permission, OCR may show empty or stale screenshots even though the app itself opens normally.

The app will also show this hint when OCR/capture fails on macOS.

## Acceptance Checklist

Run these on a real Mac before distributing the `.dmg`:

- The `.dmg` opens and contains `Teams Caption Translator.app`.
- Dragging the app to Applications works.
- Launching the app does not require the user to install Python.
- The `.app` contains `craft_mlt_25k.pth` and `japanese_g2.pth`.
- `scripts/check_macos_release.sh` passes.
- The first window opens and asks for a DeepSeek API Key when no key is saved.
- The app can save the DeepSeek key under `~/Library/Application Support/TeamsCaptionTranslator/config.json`.
- `Prepare OCR` succeeds with EasyOCR.
- `Select Region` can select the Teams caption area.
- `Test OCR` saves a debug screenshot and shows recognized Japanese text.
- `Start Translation` sends text to DeepSeek and appends Chinese lines.
- Old translated lines remain visible while new Teams rolling captions arrive.
- New lines keep the format `speaker: content`.
- Logs are written under `~/Library/Application Support/TeamsCaptionTranslator/logs`.
- `EXPORT_MACOS_SUPPORT_BUNDLE.sh` creates a diagnostics zip and redacts DeepSeek/API/key/token/secret/password fields.
- `MAC_TEST_RESULT_TEMPLATE.txt` is filled in by the tester so the manual result is traceable.
- `RELEASE_MANIFEST.json` exists and records the `.dmg` SHA256, no-Python ordinary-user requirement, support-bundle script, and macOS validation status.
- If the build source came from Windows, the Mac builder used `TeamsCaptionTranslator-v0.2.0-macos-source.zip`, not the full dirty workspace.

When the Mac builder sends back `release/TeamsCaptionTranslator-v0.2.0-macos.zip`, a Windows maintainer can run this structural audit:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\audit_macos_release_from_windows.ps1
```

That audit checks the returned zip structure, manifest, `.dmg` hash, docs, and support scripts. It still does not replace real Mac testing for Screen Recording, OCR, or Teams rolling captions.

## Known Differences From Windows

- Windows OCR is not available on macOS. Use `auto` or `easyocr`.
- The current `.dmg` is unsigned unless a Developer ID certificate is configured outside this script.
- Unsigned apps may require right-click Open on the first launch.
- Screenshot capture depends on macOS Screen Recording permission.
