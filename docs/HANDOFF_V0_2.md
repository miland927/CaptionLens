# Teams 字幕翻译器 v0.2 交接文档

## 当前目标

v0.2 的重点不是把 OCR 算法继续堆复杂，而是先把项目变成普通用户能稳定启动、能看懂状态、能定位失败原因的桌面工具。

默认流程：

1. 双击 `启动 Teams 字幕翻译器.bat`。
2. 首次自动创建 `.venv` 并安装依赖。
3. 用户输入 DeepSeek Key，测试 DeepSeek。
4. 框选 Teams 字幕区域，测试 OCR。
5. 开始翻译，翻译区持续追加 `演讲者：内容`。

## 已实现

- `scripts/run.bat` 固定使用项目 `.venv`，不再优先使用 AstrBot Python。
- `scripts/check_runtime.py` 支持运行环境检查、Windows OCR 检测和 DeepSeek Key 测试。
- `scripts/launch_app.py` 修复中文启动弹窗和日志写入。
- UI 增加“测试 DeepSeek”，并在启动后提示 Windows OCR 是否可用。
- UI 增加“准备OCR”，用于首次安装后提前初始化/诊断 EasyOCR 模型、Windows OCR 和可选 OCR 后端。
- 管线将滚动字幕按句拆分、按演讲者去重，再逐句翻译。
- 翻译区追加稳定译文；原文区作为当前 OCR 预览。
- README 已写明 `.venv`、OCR 选择、日志和 Docker 取舍。
- 安装包链路已打通：配置和日志迁移到 `%APPDATA%\TeamsCaptionTranslator`，新增 PyInstaller spec、Inno Setup 脚本、无 Inno 兜底自解压安装器和 `scripts\build_installer.ps1`。
- 当前已验证产物：`installer\TeamsCaptionTranslatorSetup-0.2.0.exe`，可静默安装到临时目录，安装后的 exe smoke 通过。
- 新增 `scripts\verify_release.ps1` 作为发布前验收入口，可自动静默安装、运行安装后 smoke test、静默卸载并检查测试安装目录已清理。
- PyInstaller spec 会从 `%USERPROFILE%\.EasyOCR\model` 或 `TCT_EASYOCR_MODEL_DIR` 收集 `craft_mlt_25k.pth` 和 `japanese_g2.pth`，随安装包分发给日语 EasyOCR 使用。
- `scripts\verify_release.ps1 -OcrSmoke` 可验证安装后的程序能初始化 OCR；最新验证结果为 `easyocr` 准备成功。
- `scripts\prepare_sandbox_release_check.ps1` 可生成 Windows Sandbox 验收包和 `.wsb` 配置，用于接近干净 Windows 的自动安装、OCR smoke 和卸载测试。

## OCR 选择建议

- `auto`：普通用户默认使用，实时优先 EasyOCR，Windows OCR 兜底。
- `easyocr`：实时字幕首选，首次模型加载慢，后续比 PowerShell Windows OCR 更适合连续使用。
- `windows`：依赖少，但当前实现每帧启动 PowerShell 子进程，实时延迟较高，适合手动测试或兜底。
- `rapidocr`：保留为可选项，不是默认依赖。

## 已知风险

- Windows OCR 仍通过 PowerShell 子进程调用，长时间实时使用会有启动开销。
- EasyOCR 对 Teams 字幕截图质量敏感，选区混入 Word、头像、工具栏时容易识别杂音。
- DeepSeek Key 保存在 `config.json`，本地使用方便，但不适合提交仓库。
- 安装版 DeepSeek Key 保存在用户目录 `%APPDATA%\TeamsCaptionTranslator\config.json`，不会写入 Program Files。
- Docker 不适合主流程，因为它默认无法访问 Windows 桌面截图、Teams 窗口和 Windows OCR。

## 后续建议

- 把 Windows OCR 改成长驻进程或 pythonnet/WinRT 直连，减少每次 OCR 的子进程开销。
- 增加日志面板或“复制诊断信息”按钮，方便远程排错。
- 给 `测试OCR` 增加截图缩略图预览，用户不用去 `logs\debug` 手动打开。
- 如果要分发给非开发用户，下一步可做 PyInstaller 打包。
- 如果目标安装包过大，再评估 Windows OCR 优先版或轻量 OCR 后端；当前 Inno 安装包约 0.25GB，因为已内置日语 EasyOCR 模型。
- 每次重打安装包后先运行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_release.ps1`，再交给非开发用户测试。
- 涉及 OCR 模型或打包 spec 改动时，运行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_release.ps1 -OcrSmoke`。
- 若机器支持 Windows Sandbox，运行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\prepare_sandbox_release_check.ps1` 后打开生成的 `.wsb`，将 `build\sandbox_release_check\results\RESULT.txt` 作为干净环境验收结果。
