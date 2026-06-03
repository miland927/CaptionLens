# Rebuild Plan

## Why Restart

The old implementation is small and useful as a prototype, but its architecture is
the main bottleneck.

Observed issues in `D:\dteamscatch\teams_caption_translator.py`:

- OCR is called through PowerShell for every frame.
- Each OCR pass writes a temporary PNG to disk.
- Capture, OCR, translation, and UI update are effectively serialized.
- Only exact text equality is cached, so OCR jitter causes repeated translation.
- Fixed interval polling cannot react well to scrolling or rapidly changing Teams
  captions.
- The UI and logs show encoding damage, which makes debugging harder.

## Target Architecture

Use a low-latency event pipeline:

```text
screen capture
  -> region crop
  -> frame change detection
  -> subtitle stability gate
  -> OCR worker
  -> text normalizer and deduper
  -> translation worker
  -> overlay / transcript UI
```

Each stage should have its own queue and latest-value semantics. If OCR or
translation falls behind, old frames should be dropped instead of building a backlog.

## MVP Scope

The first new version should do only five things well:

1. Select a screen region.
2. Capture that region at a high rate with low overhead.
3. Run OCR only when the region changes and then stabilizes.
4. Translate only new or meaningfully changed text.
5. Display current raw text, translated text, latency, and history.

Avoid adding audio translation, multiple windows, or complex prompt memory until the
basic subtitle loop is fast.

## Recommended Stack

### Option A: Python MVP

Best for quick iteration.

- Capture: `dxcam`
- Image preprocessing: `opencv-python`
- OCR: start with Windows OCR if direct WinRT is stable; otherwise RapidOCR.
- Translation: pluggable providers with local cache.
- UI: `PySide6` or `customtkinter`; avoid heavy UI work in the capture thread.

Key warning: do not call Windows OCR through PowerShell per frame.

### Option B: .NET Windows App

Best for performance and clean Windows integration.

- UI: WPF or WinUI
- OCR: Windows OCR / OneOCR direct integration
- Capture: Windows Graphics Capture or DXGI
- Translation: provider interface for Google, DeepL, OpenAI-compatible APIs, Ollama

This is likely the better long-term direction if the goal is a polished Windows
desktop tool.

## Latency Budget

Aim for:

- Capture/crop: under 20 ms
- Change detection: under 5 ms
- OCR: under 250 ms for a small subtitle region
- Translation: under 700 ms for cloud translation, under 1500 ms for local LLM
- UI update: under 16 ms

The user-perceived target is usually under 1 second from subtitle appearance to
Chinese text.

## Handling Scrolling Captions

Teams captions often roll rather than fully replace the text. Treat the OCR result
as a moving text window.

Use:

- Unicode normalization
- whitespace cleanup
- OCR confidence filtering when available
- fuzzy similarity instead of exact equality
- longest common suffix/prefix merging
- recent sentence cache with TTL

Translate only the new stable sentence or the current complete caption block,
depending on mode.

## Translation Strategy

Implement translators behind one interface:

```text
translate(text, source_lang, target_lang, context) -> TranslationResult
```

Recommended order:

1. Cache lookup by normalized text.
2. Fast free provider for MVP.
3. OpenAI-compatible provider for quality.
4. Optional local provider such as Ollama for privacy.

For Teams subtitles, short sentence fragments need context. Keep the last 3 to 5
recognized subtitle lines as context, but only display the translation for the
current line.

## First Milestone

Build a CLI/prototype loop first:

1. Capture the configured region.
2. Print FPS, frame-change events, OCR text, and timing.
3. Add translation after OCR is stable.
4. Add UI only after the loop is measurable.

This prevents UI bugs from hiding OCR/capture bottlenecks.

