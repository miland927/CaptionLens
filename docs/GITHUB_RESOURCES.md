# GitHub Resources

## Directly Useful

### DXcam

Repository: https://github.com/ra1nty/DXcam

Use for high-performance Windows screen capture. It is designed for low-latency,
high-FPS pipelines and supports DXGI plus Windows Graphics Capture backends.

Why it matters: the old project uses `mss`, which is fine for prototypes, but the
new project needs fast region capture and good pacing.

### RapidOCR

Repository: https://github.com/RapidAI/RapidOCR

Use as the first external OCR fallback. It is ONNX Runtime based, has Python
support, and is more deployment-oriented than EasyOCR.

Why it matters: EasyOCR is heavy and slow for this use case. RapidOCR is a better
candidate when Windows OCR is inaccurate or unavailable.

## Applications To Study

### Translumo

Repository: https://github.com/ramjke/Translumo

Study its product decisions: multiple OCR engines, low-latency focus, and game/app
screen overlay workflow. Its README specifically recommends Windows OCR and warns
that Tesseract and EasyOCR are slower legacy options.

### MORT

Repository: https://github.com/killkimno/MORT

Study its mature feature set: multiple OCR areas, image adjustment, machine
translation providers, custom translation API, and long-running game translation
workflow.

### RSTGameTranslation

Repository: https://github.com/thanhkeke97/RSTGameTranslation

Study its modern Windows app structure and provider list. It supports OneOCR,
Windows OCR, PaddleOCR, EasyOCR, RapidOCR, plus cloud and local translation
providers.

### WinLens

Repository: https://github.com/marco-beltrame/WinLens

Study in-place screen translation and Windows OCR integration ideas. It is closer
to a "Google Lens for Windows" workflow than a Teams-only tool.

## Do Not Copy Blindly

Many small "screen translator" repositories found in search are tiny demos or
release-only wrappers. They are useful as references, but the rebuild should prefer
well-maintained core libraries and a simple measured pipeline.

## Recommended Starting Choice

For this project, start with:

- `dxcam` for capture.
- Windows OCR direct integration for the first OCR backend.
- RapidOCR as a second OCR backend.
- A small provider interface for translation.
- Strict frame dropping and de-duplication so slow OCR/translation cannot freeze
  the UI.

