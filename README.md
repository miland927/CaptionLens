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

第一次使用按这个顺序来：

1. 输入 DeepSeek API Key，点击“保存设置”，再点“测试 DeepSeek”。
2. 点击“准备OCR”。首次使用 EasyOCR 时可能会准备模型，完成后状态会显示 OCR 是否就绪。
3. 打开 Teams 字幕，点击“选择区域”，用鼠标框住字幕出现的位置。
4. 点击“测试OCR”，能识别到原文后点击“开始翻译”。

区域、Key、语言和 OCR 引擎都会保存到 `config.json`，下次打开不用重新配置。

## 推荐设置

- 翻译：`deepseek`
- 原文：`ja`
- 译文：`zh-CN`
- OCR语言：`ja`
- OCR引擎：`auto`

`auto` 会优先使用 EasyOCR，适合实时滚动字幕；Windows OCR 只作为兜底或手动选择。日语 Teams 字幕通常先用 `auto`，如果识别很差，再手动切到 `windows` 测试。

安装包已经内置日语 EasyOCR 常用模型（`craft_mlt_25k.pth` 和 `japanese_g2.pth`），普通用户首次点击“准备OCR”时不需要再单独安装 Python 或手动下载模型。

## 怎么判断卡在哪

窗口状态会按流程变化：

```text
截图正常 -> OCR识别到文本 -> 翻译中 -> 已翻译
```

- 一直是“等待字幕”：通常是字幕区域没框准，点“测试OCR”看截图。
- OCR 有原文但没翻译：点“测试 DeepSeek”，检查 Key 或网络。
- OCR 未就绪：点“准备OCR”，看状态栏提示是 EasyOCR 模型准备失败、Windows OCR 不可用，还是依赖缺失。
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

## 构建安装包

先确认当前机器能正常运行本项目，然后执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_installer.ps1
```

构建流程会：

1. 使用 `.venv` 安装 PyInstaller。
2. 生成冻结后的桌面程序到 `dist\TeamsCaptionTranslator`。
3. 如果安装了 Inno Setup 6，继续生成标准安装包到 `installer`。
4. 如果没有 Inno Setup 6，会自动生成一个自解压用户安装包作为兜底。

当前推荐分发文件：

```text
installer\TeamsCaptionTranslatorSetup-0.2.0.exe
```

这个安装包不要求用户安装 Python。双击安装后，用户只需要输入 DeepSeek API Key、框选字幕区域、点击开始。

安装版不会把配置写到安装目录，而是写到：

```text
%APPDATA%\TeamsCaptionTranslator\config.json
%APPDATA%\TeamsCaptionTranslator\logs
```

用户首次启动后只需要输入 DeepSeek API Key、选择字幕区域、点击开始。

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

## 生成分发目录

准备把安装包发给别人前运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\prepare_release_package.ps1
```

输出目录：

```text
release\TeamsCaptionTranslator-v0.2.0
```

里面包含安装包、`SHA256.txt` 和 `QUICK_START.md`。

`QUICK_START.md` 由 Python 生成，包含中文和英文说明，避免 Windows PowerShell 编码导致中文乱码。

release 目录还包含 `CLEAN_MACHINE_CHECK.ps1`。把整个 release 目录复制到另一台 Windows 电脑后，可在该目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\CLEAN_MACHINE_CHECK.ps1
```

脚本会安装、运行普通/OCR smoke、卸载，并写入 `CLEAN_MACHINE_RESULT.txt`。

如果要在干净机器上顺手验证 DeepSeek Key 和网络，也可以运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\CLEAN_MACHINE_CHECK.ps1 -DeepSeekApiKey "sk-..."
```

## 发布就绪审计

运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\audit_release_readiness.ps1 -RunSmoke
```

它会检查安装包、分发目录、SHA256、内置 EasyOCR 模型、沙盒验收包，并运行本机安装/OCR smoke。审计报告会写入：

```text
release\RELEASE_AUDIT_v0.2.0.txt
```

## 发布前验证

打包后建议运行一次发布验证：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_release.ps1
```

这个脚本会把安装包静默安装到 `build\release_check_install`，运行安装后的程序 smoke test，然后静默卸载并检查安装目录已清理。它不会使用真实 DeepSeek Key，也不会写入真实 AppData。

需要同时验证安装后的 OCR 初始化时，运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_release.ps1 -OcrSmoke
```

## 干净 Windows 验证

如果机器支持 Windows Sandbox，可以生成一个接近干净电脑的验收包：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\prepare_sandbox_release_check.ps1
```

然后打开生成的：

```text
build\sandbox_release_check\TeamsCaptionTranslatorReleaseCheck.wsb
```

沙盒会自动安装当前安装包，运行普通启动 smoke test 和 OCR 初始化 smoke test，再卸载。结果会写回：

```text
build\sandbox_release_check\results
```
