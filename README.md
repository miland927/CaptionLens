# Teams 字幕翻译器

Windows 桌面小工具，用来框选 Microsoft Teams 的滚动字幕区域，自动截图、OCR 识别并用 DeepSeek 翻译成中文。

## 最简单用法

双击根目录里的：

```text
启动 Teams 字幕翻译器.bat
```

首次使用只做三件事：

1. 在窗口里输入 DeepSeek API Key，点击“保存设置”。
2. 打开 Teams 字幕，点击“选择区域”，用鼠标框住字幕出现的位置。
3. 点击“测试OCR”，能识别到原文后点击“开始翻译”。

区域、Key、语言和 OCR 引擎都会保存到 `config.json`，下次打开不用重新配置。

## 推荐设置

- 翻译：`deepseek`
- 原文：`ja`
- 译文：`zh-CN`
- OCR语言：`ja`
- OCR引擎：`auto`

`auto` 会优先使用 Windows 内置 OCR；如果不可用，再尝试 EasyOCR 和 RapidOCR。

## 调试 OCR

点击“测试OCR”会临时隐藏窗口，截取当前字幕区域，并把截图保存到：

```text
logs\debug
```

如果截图里没有字幕，说明选区不对，重新点“选择区域”即可。如果截图里有字幕但识别很差，可以把 OCR 引擎从 `auto` 切到 `windows`、`easyocr` 或 `rapidocr` 试试。

## 日志

双击后没有正常打开时，查看：

```text
logs\launcher.log
logs\app.log
```

## 开发运行

```bat
scripts\run.bat
```

或：

```bat
set PYTHONPATH=%CD%\src
python -m teams_caption_translator.main
```

## 当前架构

```text
screen capture
  -> frame change detection
  -> stability gate
  -> OCR worker
  -> text normalization / dedupe
  -> translation worker
  -> overlay UI
```

0.2 版本重点：

- DeepSeek 作为默认翻译器，并可在 UI 直接输入 API Key
- OCR 预处理增强：放大、自动对比度、锐化、直方图阈值和明暗背景自适应
- UI 可配置翻译器、语言和 OCR 引擎
- 缺少 DeepSeek Key 时在 UI 提示，不再让后台线程静默失败
