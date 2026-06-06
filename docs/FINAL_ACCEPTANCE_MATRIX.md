# Final Acceptance Matrix

This file defines the hard stop for the v0.2 packaging goal:

> A normal user on Windows or macOS can install the app without installing Python, paste a DeepSeek API key, select the Microsoft Teams caption region, and get stable Chinese translations.

Until every required row below has evidence, the full goal is not complete.

## Current Status

| Area | Status | Evidence | Remaining work |
| --- | --- | --- | --- |
| Windows installer exists | Done | `installer/TeamsCaptionTranslatorSetup-0.2.0.exe` | Rebuild after release-doc changes if distributing a fresh zip |
| Windows release zip exists | Done | `release/TeamsCaptionTranslator-v0.2.0-windows.zip` | Run on clean external Windows machine |
| Windows no-Python install | Mostly done | PyInstaller/Inno package plus `CLEAN_MACHINE_CHECK.ps1` | Verify on clean Windows/VM/Sandbox outside this dev machine |
| Windows OCR models bundled | Done | `dist/TeamsCaptionTranslator/_internal/easyocr_model` | Re-check after every rebuild |
| Windows DeepSeek smoke | Partially verified | Smoke hook exists | Run with a real key on clean machine |
| Windows real Teams captions | Not fully verified | Manual checklist exists | Run `MANUAL_TEAMS_CHECK.md` in a real Teams meeting |
| Windows support bundle | Done | `EXPORT_SUPPORT_BUNDLE.ps1` redacts secrets | Confirm tester can export and send bundle |
| macOS app build script | Drafted | `scripts/build_macos.sh` | Run on a real Mac |
| macOS clean source package | Prepared | `scripts/prepare_macos_source_package.ps1` | Send package to a real Mac builder and build from it |
| macOS source package manifest | Prepared | Source package includes `SOURCE_PACKAGE_MANIFEST.json`; release folder gets `*.SOURCE_PACKAGE_MANIFEST.json` | Confirm manifest hash matches the source zip |
| macOS build Python version gate | Prepared, not verified on Mac | `scripts/build_macos.sh` checks Python 3.10+ before venv creation | Run on a real Mac |
| macOS release check script | Drafted | `scripts/check_macos_release.sh` | Run on a real Mac |
| macOS release package script | Drafted | `scripts/prepare_macos_release.sh` | Run on a real Mac |
| macOS no-Python install | Not verified | PyInstaller `.app` spec exists | Build `.app`/`.dmg` and test on Mac without source venv |
| macOS OCR models bundled | Prepared, not verified on Mac | `scripts/build_macos.sh` prepares models and checks `.app`; `scripts/check_macos_release.sh` checks `.app` | Run scripts on a real Mac |
| macOS Screen Recording flow | Not verified | UI hint and docs exist | Grant permission and verify screenshot capture |
| macOS OCR/DeepSeek/Teams flow | Not verified | Scripts and docs exist | Test real Teams rolling captions |
| macOS support bundle | Prepared, not verified on Mac | `scripts/export_macos_support_bundle.sh` | Run from macOS release folder after app logs exist |
| macOS release manifest | Prepared, not verified on Mac | `scripts/prepare_macos_release.sh` writes `RELEASE_MANIFEST.json` | Confirm manifest exists in final macOS zip |
| macOS returned-package audit | Prepared | `scripts/audit_macos_release_from_windows.ps1` | Run after a real Mac returns `TeamsCaptionTranslator-v0.2.0-macos.zip` |
| macOS manual test report | Prepared | `docs/MAC_TEST_RESULT_TEMPLATE.txt` | Tester fills it after real Mac / real Teams validation |

## Windows Acceptance

Required evidence before Windows is considered complete:

1. `scripts/audit_release_readiness.ps1` passes, except a host may lack Windows Sandbox.
2. `scripts/verify_release.ps1 -OcrSmoke` passes after the latest release package was generated.
3. `release/TeamsCaptionTranslator-v0.2.0/CLEAN_MACHINE_CHECK.ps1` passes on a clean Windows machine.
4. The same clean-machine check passes with `-DeepSeekApiKey "sk-..."`.
5. `MANUAL_TEAMS_CHECK.md` passes in a real Teams rolling-caption session.
6. Old translated content remains visible while new subtitles append.
7. New translated lines keep `speaker: content` formatting.
8. A support bundle can be exported without exposing the DeepSeek key.

## macOS Acceptance

Required evidence before macOS is considered complete:

1. On a real Mac, run:

   ```bash
   bash scripts/build_macos.sh
   ```

2. Confirm these files exist:

   ```text
   dist-macos/Teams Caption Translator.app
   release/TeamsCaptionTranslator-v0.2.0-macos.dmg
   ```

3. Run:

   ```bash
   bash scripts/check_macos_release.sh
   bash scripts/prepare_macos_release.sh
   ```

4. Confirm the release zip exists:

   ```text
   release/TeamsCaptionTranslator-v0.2.0-macos.zip
   ```

5. Install from the `.dmg` on a Mac where the user has not installed project dependencies.
6. Confirm the generated `.app` contains `craft_mlt_25k.pth` and `japanese_g2.pth`.
7. Launch the app, paste a DeepSeek key, and save it under:

   ```text
   ~/Library/Application Support/TeamsCaptionTranslator/config.json
   ```

8. Grant Screen Recording permission when needed, then restart the app.
9. Confirm screenshot capture sees the Teams caption region.
10. Confirm EasyOCR recognizes Japanese captions.
11. Confirm DeepSeek translation appends Chinese lines.
12. Confirm old translated content remains visible while new subtitles append.
13. Confirm logs are written under:

   ```text
   ~/Library/Application Support/TeamsCaptionTranslator/logs
   ```
14. Run `./EXPORT_MACOS_SUPPORT_BUNDLE.sh` from the macOS release folder and confirm the generated zip does not expose the DeepSeek key.
15. Confirm `RELEASE_MANIFEST.json` exists in the macOS release folder and records the `.dmg` hash, no-Python requirement, support-bundle script, and validation status.
16. Fill `MAC_TEST_RESULT_TEMPLATE.txt` with the real Mac result.
17. After the Mac builder sends back `TeamsCaptionTranslator-v0.2.0-macos.zip`, run this on Windows:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\audit_macos_release_from_windows.ps1
   ```

## Distribution Standard

Only distribute both platforms as complete when both files are produced and verified:

```text
TeamsCaptionTranslator-v0.2.0-windows.zip
TeamsCaptionTranslator-v0.2.0-macos.zip
```

Before that, describe the current package honestly as Windows-only, with macOS packaging prepared but not validated.
