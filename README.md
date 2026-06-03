# Teams 字幕翻译器

Windows 桌面小工具，用来框选 Microsoft Teams 的滚动字幕区域，自动截图、OCR 识别，并用 DeepSeek 翻译成中文。

## 最简单用法

双击根目录里的：

```text
启动 Teams 字幕翻译器.bat
```

首次运行会自动创建项目专属环境：

```text
.venv
```

以后都固定用这个环境启动，不再混用 AstrBot 或其他项目的 Python。

第一次使用只做三件事：

1. 输入 DeepSeek API Key，点击“保存设置”，再点“测试 DeepSeek”。
2. 打开 Teams 字幕，点击“选择区域”，用鼠标框住字幕出现的位置。
3. 点击“测试OCR”，能识别到原文后点击“开始翻译”。

区域、Key、语言和 OCR 引擎都会保存到 `config.json`，下次打开不用重新配置。

## 推荐设置

- 翻译：`deepseek`
- 原文：`ja`
- 译文：`zh-CN`
- OCR语言：`ja`
- OCR引擎：`auto`

`auto` 会优先使用 EasyOCR，适合实时滚动字幕；Windows OCR 只作为兜底或手动选择。日语 Teams 字幕通常先用 `auto`，如果识别很差，再手动切到 `windows` 测试。

## 怎么判断卡在哪

窗口状态会按流程变化：

```text
截图正常 -> OCR识别到文本 -> 翻译中 -> 已翻译
```

- 一直是“等待字幕”：通常是字幕区域没框准，点“测试OCR”看截图。
- OCR 有原文但没翻译：点“测试 DeepSeek”，检查 Key 或网络。
- 翻译重复或跳动：清空后重新选择更窄的字幕区域，尽量只框字幕列表，不要框到 Word、参会者头像或工具栏。

## 调试 OCR

点击“测试OCR”会临时隐藏窗口，截取当前字幕区域，并把截图保存到：

```text
logs\debug
```

如果截图里没有字幕，说明选区不对，重新点“选择区域”。如果截图里有字幕但识别很差，可以把 OCR 引擎从 `auto` 切到 `windows` 试试。

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

或使用已经创建好的虚拟环境：

```bat
.venv\Scripts\python.exe -m teams_caption_translator.main
```

## Docker 说明

Docker 不作为本项目默认运行方案。这个工具需要访问 Windows 桌面截图、Teams 窗口、Tkinter UI 和 Windows OCR；这些能力在 Docker 里默认不可用。Docker 只适合后端单元测试，不适合主流程。

## 当前架构

```text
screen capture
  -> frame change detection
  -> stability gate
  -> OCR worker
  -> caption parse / sentence split / dedupe
  -> translation worker
  -> transcript UI
```

0.2 版本重点：

- 使用项目专属 `.venv`，避免本地 Python 依赖冲突
- DeepSeek 作为默认翻译器，并可在 UI 直接输入和测试 API Key
- OCR 预处理增强，并显示实际 OCR 引擎和截图调试路径
- 翻译区按 `演讲者：内容` 追加，滚动字幕刷新不覆盖旧翻译
