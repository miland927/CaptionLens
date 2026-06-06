Teams 字幕翻译器 macOS 说明

当前 macOS 版本必须在真实 Mac 上构建和验证。

构建完成后，目标文件应为：

release/TeamsCaptionTranslator-v0.2.0-macos.dmg

安装方法：

1. 双击 TeamsCaptionTranslator-v0.2.0-macos.dmg。
2. 把 Teams Caption Translator.app 拖到 Applications。
3. 第一次打开时，如果 macOS 阻止未签名应用，请右键 app，选择 Open。
4. 打开 System Settings。
5. 进入 Privacy & Security。
6. 进入 Screen Recording。
7. 勾选 Teams Caption Translator。
8. 退出并重新打开 Teams Caption Translator。

第一次使用：

1. 输入你自己的 DeepSeek API Key。
2. 点击 Test DeepSeek。
3. 点击 Prepare OCR。
4. 打开 Microsoft Teams 字幕。
5. 点击 Select Region，框住字幕滚动区域。
6. 点击 Test OCR。
7. 点击 Start Translation。

如果 OCR 没有文字：

- 先确认 Screen Recording 权限已经开启。
- 退出并重开 Teams Caption Translator。
- 重新选择字幕区域。
- 再点 Test OCR。

如果测试失败：

请不要截图或发送 DeepSeek Key。

在 release 文件夹里运行：

./EXPORT_MACOS_SUPPORT_BUNDLE.sh

它会生成 TeamsCaptionTranslatorSupport-*.zip，里面包含日志和脱敏后的配置，不包含明文 DeepSeek Key。

日志位置：

~/Library/Application Support/TeamsCaptionTranslator/logs

注意：

- macOS 没有 Windows OCR，默认使用 EasyOCR。
- 当前 macOS 包如果未签名，第一次打开可能需要右键 Open。
- macOS 包必须在真实 Mac 上通过 scripts/check_macos_release.sh 和真实 Teams 字幕测试后才能分发。
