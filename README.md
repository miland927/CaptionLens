# Teams 字幕翻译器

用于 Microsoft Teams 滚动字幕的桌面翻译工具。用户框选 Teams 字幕区域后，程序会自动截图、OCR 识别、调用 DeepSeek 翻译，并把中文结果追加显示。

目标体验：

```text
双击安装包 -> 输入 DeepSeek API Key -> 框选 Teams 字幕 -> 开始翻译
```

## 当前平台状态

### Windows

Windows 安装包已接近可分发状态。

推荐发给 Windows 用户的文件：

```text
release\TeamsCaptionTranslator-v0.2.0-windows.zip
```

用户解压后双击：

```text
TeamsCaptionTranslatorSetup-0.2.0.exe
```

Windows 用户不需要安装 Python，也不需要手动下载 OCR 模型。安装包已经包含冻结后的 Python 运行时、应用代码和常用日语 EasyOCR 模型。

### macOS

macOS 打包脚本和说明已经准备好，但还没有在真实 Mac 上完成 `.app` / `.dmg` 构建和验证。

macOS 必须在真实 Mac 上运行：

```bash
bash scripts/build_macos.sh
bash scripts/check_macos_release.sh
bash scripts/prepare_macos_release.sh
```

完成前不能把 macOS 版本说成已交付。详见：

```text
docs\MACOS_PACKAGING.md
docs\FINAL_ACCEPTANCE_MATRIX.md
```

如果需要从 Windows 机器准备一个干净源码包发给 Mac 构建者，运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\prepare_macos_source_package.ps1
```

生成的 `release\TeamsCaptionTranslator-v0.2.0-macos-source.zip` 会排除 `.venv`、`build`、`dist`、`release`、`logs` 和本地 `config.json`。

同目录还会生成 `TeamsCaptionTranslator-v0.2.0-macos-source.SOURCE_PACKAGE_MANIFEST.json`，用于核对源码包哈希、排除规则和 Mac 构建命令。

Mac 构建者完成后，把 `release/TeamsCaptionTranslator-v0.2.0-macos.zip` 传回。维护者可在 Windows 上运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\audit_macos_release_from_windows.ps1
```

这个脚本会检查 Mac 回传 zip 的 manifest、dmg 哈希、说明文档和支持包脚本，但不能代替真实 Mac 上的截图/OCR/Teams 验证。

### Docker

Docker 不作为主方案。这个项目需要访问用户桌面截图、Teams 窗口、Tkinter UI 和系统权限；Docker 默认不适合桌面截图/OCR 主流程。

## 普通用户使用方法

1. 安装并打开 Teams Caption Translator。
2. 粘贴自己的 DeepSeek API Key。
3. 点击 `Test DeepSeek`。
4. 点击 `Prepare OCR`。
5. 打开 Microsoft Teams 字幕。
6. 点击 `Select Region`，框住字幕滚动区域。
7. 点击 `Test OCR`，确认能看到日语原文。
8. 点击 `Start Translation`。

推荐设置：

```text
翻译器: deepseek
原文: ja
译文: zh-CN
OCR 语言: ja
OCR 引擎: auto
```

翻译区会按下面格式追加，不会因为新字幕刷新而清空旧内容：

```text
演讲者：内容
```

字幕不会把每一张截图都直接送去翻译。程序会先把 Teams 滚动字幕做约 1 秒的稳定确认，合并同一演讲者的连续 OCR 更新，再只把新增稳定字幕提交给 DeepSeek。这样可以减少重复翻译、断句、旧内容刷屏和 token 浪费。

送翻译前还会做一次字幕质量过滤。明显不是字幕的 OCR 行会被丢弃，例如日期时间、纯数字/分数、以数字开头的头像标签、Teams 内部编号样式，以及符号和拉丁字母混入明显的 OCR 乱码。过滤只影响 DeepSeek 输入和当前字幕预览，不会保存额外截图。

`Test OCR` 保存的调试截图位于：

```text
Windows: %APPDATA%\TeamsCaptionTranslator\logs\debug
macOS:   ~/Library/Application Support/TeamsCaptionTranslator/logs/debug
```

默认只保留最近 30 张，或最多约 100MB。程序里也有“重置数据”按钮，可删除已保存的 Key、字幕区域、日志和 OCR 调试截图，方便测试版本反复验证。

## 出问题时

Windows 用户可在 release 文件夹运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\EXPORT_SUPPORT_BUNDLE.ps1
```

macOS 用户可在 release 文件夹运行：

```bash
./EXPORT_MACOS_SUPPORT_BUNDLE.sh
```

支持包会复制日志并脱敏配置中的 API/key/token/secret/password 字段。不要手动把 DeepSeek Key 发给维护者。

日志位置：

```text
Windows: %APPDATA%\TeamsCaptionTranslator\logs
macOS:   ~/Library/Application Support/TeamsCaptionTranslator/logs
```

## Windows 打包

构建 Windows 安装包：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_installer.ps1
```

生成 release 文件夹和 zip：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\prepare_release_package.ps1
```

本机安装/OCR smoke 验证：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_release.ps1 -OcrSmoke
```

发布审计：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\audit_release_readiness.ps1 -RunSmoke
```

如果这台机器没有 Windows Sandbox，审计会在 `Windows Sandbox available on this host` 一项失败。这是宿主机能力限制，不代表安装包本身失败。

## 干净 Windows 验证

把下面文件发到干净 Windows 机器、Windows VM 或 Windows Sandbox：

```text
release\TeamsCaptionTranslator-v0.2.0-windows.zip
```

解压后运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\CLEAN_MACHINE_CHECK.ps1 -DeepSeekApiKey "sk-..."
```

然后按照 `MANUAL_TEAMS_CHECK.md` 做一次真实 Teams 滚动字幕测试。

## macOS 打包

只能在真实 Mac 上构建可信 macOS 包：

```bash
cd "/path/to/Dmsch v0.2"
bash scripts/build_macos.sh
bash scripts/check_macos_release.sh
bash scripts/prepare_macos_release.sh
```

目标产物：

```text
release/TeamsCaptionTranslator-v0.2.0-macos.zip
```

macOS 用户第一次运行时通常需要授予 Screen Recording 权限，否则截图和 OCR 会失败。

## 最终完成标准

以这个文件为准：

```text
docs\FINAL_ACCEPTANCE_MATRIX.md
```

只有当 Windows 和 macOS 都满足下面条件时，才算完整达成目标：

- 用户不需要安装 Python。
- 用户只需安装、输入 DeepSeek Key、框选 Teams 字幕区域。
- OCR 能识别日语 Teams 滚动字幕。
- DeepSeek 翻译能稳定输出中文。
- 旧翻译保留，新字幕按 `演讲者：内容` 追加。
- 测试失败时能导出脱敏支持包。

## 开发运行

源码开发模式需要本机有普通 Python 3.10+：

```bat
scripts\run.bat
```

`scripts\run.bat` 会创建项目专属 `.venv`，并避免使用 AstrBot 的 Python。

注意：开发环境需要 Python，但最终安装包不要求普通用户安装 Python。
