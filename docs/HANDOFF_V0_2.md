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
- 管线将滚动字幕按句拆分、按演讲者去重，再逐句翻译。
- 翻译区追加稳定译文；原文区作为当前 OCR 预览。
- README 已写明 `.venv`、OCR 选择、日志和 Docker 取舍。

## OCR 选择建议

- `auto`：普通用户默认使用，实时优先 EasyOCR，Windows OCR 兜底。
- `easyocr`：实时字幕首选，首次模型加载慢，后续比 PowerShell Windows OCR 更适合连续使用。
- `windows`：依赖少，但当前实现每帧启动 PowerShell 子进程，实时延迟较高，适合手动测试或兜底。
- `rapidocr`：保留为可选项，不是默认依赖。

## 已知风险

- Windows OCR 仍通过 PowerShell 子进程调用，长时间实时使用会有启动开销。
- EasyOCR 对 Teams 字幕截图质量敏感，选区混入 Word、头像、工具栏时容易识别杂音。
- DeepSeek Key 保存在 `config.json`，本地使用方便，但不适合提交仓库。
- Docker 不适合主流程，因为它默认无法访问 Windows 桌面截图、Teams 窗口和 Windows OCR。

## 后续建议

- 把 Windows OCR 改成长驻进程或 pythonnet/WinRT 直连，减少每次 OCR 的子进程开销。
- 增加日志面板或“复制诊断信息”按钮，方便远程排错。
- 给 `测试OCR` 增加截图缩略图预览，用户不用去 `logs\debug` 手动打开。
- 如果要分发给非开发用户，下一步可做 PyInstaller 打包。
