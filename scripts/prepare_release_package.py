from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def build_start_here(version: str, installer_name: str) -> str:
    windows_zip = f"TeamsCaptionTranslator-v{version}-windows.zip"
    return f"""START HERE - Teams Caption Translator v{version}

Platform:

- This zip is for Windows.
- Recommended file to send: {windows_zip}
- Windows users do not need Python.
- macOS is not included in this zip. See PLATFORM_SUPPORT.md.

For normal users:

1. Double-click {installer_name}
2. Keep the default installer options.
3. When the app opens, paste your DeepSeek API Key.
4. Click "Test DeepSeek".
5. Click "Prepare OCR".
6. Open Microsoft Teams captions.
7. Click "Select Region" and drag around the caption area.
8. Click "Test OCR".
9. Click "Start Translation".

Notes:

- The installer uses English on purpose to avoid garbled text on different Windows machines.
- A desktop shortcut is created by default.
- Python is not required on the user's computer.
- Japanese EasyOCR models are bundled.
- To collect safe diagnostics, run EXPORT_SUPPORT_BUNDLE.ps1.
- Before broad distribution, run MANUAL_TEAMS_CHECK.md in a real Teams rolling-caption session.
"""


def build_readme_cn(version: str, installer_name: str) -> str:
    windows_zip = f"TeamsCaptionTranslator-v{version}-windows.zip"
    return f"""Teams 字幕翻译器 v{version} 中文说明

这是 Windows 安装包。

推荐发送和使用：

{windows_zip}

Windows 用户不需要安装 Python，也不需要手动下载 OCR 模型。

安装方法：

1. 解压 {windows_zip}
2. 双击 {installer_name}
3. 安装选项保持默认
4. 安装完成后程序会自动打开，也可以从桌面图标打开

第一次使用：

1. 在 DeepSeek Key 输入框里粘贴你的 DeepSeek API Key
2. 点击“保存设置”
3. 点击“测试 DeepSeek”
4. 点击“准备 OCR”或 Prepare OCR
5. 打开 Microsoft Teams 字幕
6. 点击“选择区域”，框住 Teams 字幕滚动区域
7. 点击“测试 OCR”
8. 点击“开始翻译”

如果没有翻译：

- 先点击“测试 OCR”，确认原文区能看到日语字幕
- 如果 OCR 原文为空，重新点击“选择区域”，只框字幕区域
- 如果 OCR 有原文但没有中文，点击“测试 DeepSeek”，检查 Key 或网络

如果程序出问题：

请不要截图或发送 DeepSeek Key。

在这个解压文件夹里运行：

powershell -NoProfile -ExecutionPolicy Bypass -File .\\EXPORT_SUPPORT_BUNDLE.ps1

然后把生成的 TeamsCaptionTranslatorSupport-*.zip 发给维护者。

更多说明：

- START_HERE.txt：最短英文安装流程
- QUICK_START.md：中英文快速使用
- MANUAL_TEAMS_CHECK.md：正式验收清单
- PLATFORM_SUPPORT.md：平台支持说明
- SEND_TO_TESTER.txt：维护者可复制给测试者的说明
- RELEASE_MANIFEST.json：机器可读的版本、平台和哈希信息

注意：

当前这个包是 Windows 版。macOS 版本需要另外在真实 Mac 上构建和验证。
"""


def build_quick_start(version: str, installer_name: str) -> str:
    generic_zip = f"TeamsCaptionTranslator-v{version}.zip"
    windows_zip = f"TeamsCaptionTranslator-v{version}-windows.zip"
    return f"""# Teams 字幕翻译器 v{version} 快速使用

## 平台

这个 zip 是 Windows installer package。Windows 用户不需要安装 Python。

macOS 需要单独在真实 Mac 上构建 `.app` / `.dmg`，并验证 Screen Recording 权限、截图和 EasyOCR。详情见 `PLATFORM_SUPPORT.md`。

## 分发

推荐发送 `{windows_zip}`。`{generic_zip}` 是兼容旧说明保留的副本。

## 安装

双击：

```text
{installer_name}
```

The installer wizard intentionally uses English to avoid text-encoding issues on different Windows machines.

## 第一次使用

1. 输入 DeepSeek API Key。
2. 点击“保存设置”。
3. 点击“测试 DeepSeek”，确认 Key 和网络可用。
4. 点击“Prepare OCR”或“准备 OCR”，确认 OCR 就绪。
5. 打开 Microsoft Teams 字幕。
6. 点击“选择区域”，框住 Teams 字幕滚动区域。
7. 点击“测试 OCR”，确认能识别原文。
8. 点击“开始翻译”。

## OCR 说明

安装包已内置日语 EasyOCR 模型。普通用户不需要安装 Python，也不需要手动下载 OCR 模型。

## 最终验收

如果要确认它真的适合发给别人，请看 `MANUAL_TEAMS_CHECK.md`。自动脚本能检查安装、启动、OCR 和 DeepSeek API；真实 Teams rolling captions 仍建议人工跑一次。

## 日志位置

```text
%APPDATA%\\TeamsCaptionTranslator\\logs
```

## 支持包

如果程序无法启动、OCR 为空、或翻译失败，请运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\\EXPORT_SUPPORT_BUNDLE.ps1
```

支持包会脱敏配置，不会包含明文 DeepSeek Key。

## Clean Machine Check

在干净 Windows 机器、VM 或 Sandbox 上验证时运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\\CLEAN_MACHINE_CHECK.ps1
```

# Teams Caption Translator v{version} Quick Start

## Platform

This zip is the Windows installer package. Windows users do not need to install Python.

macOS must be built and validated separately on a real Mac. See `PLATFORM_SUPPORT.md`.

## First Run

1. Enter your DeepSeek API Key.
2. Click "Save Settings".
3. Click "Test DeepSeek".
4. Click "Prepare OCR".
5. Open Microsoft Teams captions.
6. Click "Select Region".
7. Click "Test OCR".
8. Click "Start Translation".
"""


def build_platform_support(version: str) -> str:
    generic_zip = f"TeamsCaptionTranslator-v{version}.zip"
    windows_zip = f"TeamsCaptionTranslator-v{version}-windows.zip"
    return f"""# Platform Support - Teams Caption Translator v{version}

## Windows

This release zip is for Windows.

- Recommended file to send: `{windows_zip}`
- Compatibility copy: `{generic_zip}`
- Installer: `TeamsCaptionTranslatorSetup-{version}.exe`
- User Python requirement: not required
- Bundled runtime: frozen Python application
- Bundled OCR assets: Japanese EasyOCR model files
- Config/log location: `%APPDATA%\\TeamsCaptionTranslator`

Windows validation included in this package:

- `CLEAN_MACHINE_CHECK.ps1`
- `MANUAL_TEAMS_CHECK.md`
- `EXPORT_SUPPORT_BUNDLE.ps1`
- `RELEASE_MANIFEST.json`

## macOS

macOS is not included in this Windows release zip.

The repository has macOS packaging scaffolding:

- `packaging/teams-caption-translator-macos.spec`
- `scripts/build_macos.sh`
- `scripts/check_macos_release.sh`
- `scripts/prepare_macos_release.sh`
- `scripts/export_macos_support_bundle.sh`
- `docs/MACOS_PACKAGING.md`

But the macOS package must be built and verified on a real Mac before distribution.

Required macOS evidence before release:

- `.app` launches without user-installed Python.
- `.dmg` installs cleanly.
- `scripts/check_macos_release.sh` passes.
- macOS Screen Recording permission is documented and works.
- Screenshot capture sees the Teams caption area.
- EasyOCR initializes and recognizes Japanese captions.
- DeepSeek translation works.
- Rolling captions append as `speaker: content` without clearing old translated lines.
- `EXPORT_MACOS_SUPPORT_BUNDLE.sh` creates a redacted diagnostics zip.

Until those checks pass on a real Mac, describe this package as Windows-only.
"""


def build_send_to_tester(version: str, installer_name: str) -> str:
    windows_zip = f"TeamsCaptionTranslator-v{version}-windows.zip"
    return f"""给测试者/普通用户的说明，可直接复制发送。

请使用 Windows 电脑测试这个工具。

下载并解压：

{windows_zip}

然后双击：

{installer_name}

安装完成后按这个顺序操作：

1. 打开 Teams Caption Translator。
2. 输入你自己的 DeepSeek API Key。
3. 点击 Test DeepSeek。
4. 点击 Prepare OCR。
5. 打开 Microsoft Teams 字幕。
6. 点击 Select Region，框住 Teams 字幕滚动区域。
7. 点击 Test OCR。
8. 点击 Start Translation。

你不需要安装 Python，也不需要手动下载 OCR 模型。

如果出现问题，请不要截图或发送 DeepSeek Key。

Do not send your DeepSeek Key.

请在解压后的文件夹里运行：

powershell -NoProfile -ExecutionPolicy Bypass -File .\\EXPORT_SUPPORT_BUNDLE.ps1

然后把生成的 TeamsCaptionTranslatorSupport-*.zip 发给维护者。

如果你是在做正式验收，请再看：

MANUAL_TEAMS_CHECK.md

注意：

- 这个包目前是 Windows 版。
- macOS 版本需要另外在 Mac 上构建和验证。
- 安装向导是英文，这是为了避免不同 Windows 机器上中文乱码。
"""


def build_manual_teams_check(version: str, installer_name: str) -> str:
    return f"""# Teams 字幕翻译器 v{version} 人工验收清单

这个清单用于最后确认“普通用户双击安装，输入 DeepSeek Key，就能使用”的目标。自动脚本已经能测安装、启动、OCR 初始化和 DeepSeek API；真实 Teams rolling captions 仍建议人工跑一次。

## 机器要求

- 使用一台干净 Windows 用户环境、Windows VM，或 Windows Sandbox。
- 不依赖项目源码目录。
- 不要求用户安装 Python。
- 不要求用户手动下载 OCR 模型。

## 自动检查

在解压后的 release 文件夹里运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\\CLEAN_MACHINE_CHECK.ps1 -DeepSeekApiKey "sk-..."
```

通过标准：

- `CLEAN_MACHINE_RESULT.txt` 内容是 `PASS`。
- 日志里包含 `App smoke exit code: 0`。
- 日志里包含 `First-run UI smoke exit code: 0`。
- 日志里包含 `OCR smoke exit code: 0`。
- 传入真实 key 时，日志里包含 `DeepSeek smoke exit code: 0`。

## 人工 Teams 检查

1. 双击 `{installer_name}` 安装。
2. 保持默认安装选项。
3. 打开 `Teams Caption Translator`。
4. 输入 DeepSeek API Key。
5. 点击“保存设置”。
6. 点击“测试 DeepSeek”，确认显示成功。
7. 点击“准备 OCR”，确认 OCR 引擎就绪。
8. 打开 Microsoft Teams，开启日语字幕。
9. 点击“选择区域”，框住 Teams 的滚动字幕区域。
10. 点击“测试 OCR”，确认“当前 OCR 原文”能看到日语字幕。
11. 点击“开始翻译”。
12. 等待至少 2 分钟真实会议字幕滚动。

通过标准：

- 中文翻译区持续追加内容，不清空旧内容。
- 排版保持 `演讲者：内容`。
- 新字幕出现时旧翻译不会被刷新打乱。
- OCR 延迟和翻译延迟在可接受范围内。
- 退出并重开应用后，DeepSeek Key 和常用配置仍保留。
- Acceptance keywords for audit: rolling captions, old content preserved, speaker colon content.

## 出问题时

如果测试失败，运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\\EXPORT_SUPPORT_BUNDLE.ps1
```

把生成的 `TeamsCaptionTranslatorSupport-*.zip` 交给维护者。这个包会脱敏配置里的 key/token/secret/password 字段。
"""


def build_support_bundle_exporter() -> str:
    return r"""param(
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $OutputDir.Trim()) {
    $OutputDir = $Root
}

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$WorkDir = Join-Path $OutputDir "TeamsCaptionTranslatorSupport-$Stamp"
$ZipPath = Join-Path $OutputDir "TeamsCaptionTranslatorSupport-$Stamp.zip"
$AppRoot = Join-Path $env:APPDATA "TeamsCaptionTranslator"
$LogDir = Join-Path $AppRoot "logs"
$ConfigPath = Join-Path $AppRoot "config.json"

function Redact-Object($Value) {
    if ($null -eq $Value) { return $null }
    if ($Value -is [System.Collections.IDictionary]) {
        $result = [ordered]@{}
        foreach ($key in $Value.Keys) {
            if ([string]$key -match '(?i)(api|key|token|secret|password)') {
                $result[$key] = "***REDACTED***"
            } else {
                $result[$key] = Redact-Object $Value[$key]
            }
        }
        return $result
    }
    if ($Value -is [pscustomobject]) {
        $result = [ordered]@{}
        foreach ($prop in $Value.PSObject.Properties) {
            if ($prop.Name -match '(?i)(api|key|token|secret|password)') {
                $result[$prop.Name] = "***REDACTED***"
            } else {
                $result[$prop.Name] = Redact-Object $prop.Value
            }
        }
        return $result
    }
    if (($Value -is [System.Collections.IEnumerable]) -and -not ($Value -is [string])) {
        return @($Value | ForEach-Object { Redact-Object $_ })
    }
    return $Value
}

Remove-Item -LiteralPath $WorkDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

try {
    $osInfo = Get-CimInstance Win32_OperatingSystem
    $osCaption = $osInfo.Caption
    $osVersion = $osInfo.Version
} catch {
    $osCaption = [System.Environment]::OSVersion.Platform.ToString()
    $osVersion = [System.Environment]::OSVersion.Version.ToString()
}

$systemInfo = [ordered]@{
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    os = $osCaption
    os_version = $osVersion
    architecture = $env:PROCESSOR_ARCHITECTURE
    appdata_exists = (Test-Path $AppRoot)
    logs_exist = (Test-Path $LogDir)
    config_exists = (Test-Path $ConfigPath)
}
$systemInfo | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $WorkDir "system.json") -Encoding UTF8

if (Test-Path $LogDir) {
    try {
        Copy-Item -LiteralPath $LogDir -Destination (Join-Path $WorkDir "logs") -Recurse -Force
    } catch {
        "Log directory existed, but could not be copied: $($_.Exception.Message)" | Set-Content -Path (Join-Path $WorkDir "logs.copy_failed.txt") -Encoding UTF8
    }
}

if (Test-Path $ConfigPath) {
    try {
        $config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $redacted = Redact-Object $config
        $redacted | ConvertTo-Json -Depth 20 | Set-Content -Path (Join-Path $WorkDir "config.redacted.json") -Encoding UTF8
    } catch {
        "Config existed, but could not be parsed as JSON. Raw config was not copied." | Set-Content -Path (Join-Path $WorkDir "config.redacted.txt") -Encoding UTF8
    }
}

"This support bundle redacts fields matching api/key/token/secret/password. Do not add your DeepSeek key manually." | Set-Content -Path (Join-Path $WorkDir "README.txt") -Encoding UTF8

Remove-Item -LiteralPath $ZipPath -Force -ErrorAction SilentlyContinue
Compress-Archive -LiteralPath $WorkDir -DestinationPath $ZipPath -Force
Remove-Item -LiteralPath $WorkDir -Recurse -Force

Write-Host "Support bundle created:"
Write-Host $ZipPath
"""


def build_clean_machine_check(installer_name: str) -> str:
    return f"""param(
    [string]$DeepSeekApiKey = ""
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Installer = Join-Path $Root "{installer_name}"
$Result = Join-Path $Root "CLEAN_MACHINE_RESULT.txt"
$Log = Join-Path $Root "CLEAN_MACHINE_CHECK.log"
$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\\Teams Caption Translator Clean Check"
$AppDataDir = Join-Path $env:TEMP "TeamsCaptionTranslatorCleanCheckAppData"

function Write-CheckLog([string]$Message) {{
    $line = "[{{0}}] {{1}}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Host $line
}}

function Invoke-CheckedProcess([string]$FilePath, [string[]]$Arguments, [string]$Label) {{
    Write-CheckLog "$Label: $FilePath $($Arguments -join ' ')"
    $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -Wait -PassThru -WindowStyle Hidden
    Write-CheckLog "$Label exit code: $($process.ExitCode)"
    if ($process.ExitCode -ne 0) {{ throw "$Label failed with code $($process.ExitCode)" }}
}}

try {{
    Remove-Item -LiteralPath $Result -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $Log -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $AppDataDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $AppDataDir | Out-Null

    if (-not (Test-Path $Installer)) {{ throw "Installer not found: $Installer" }}

    $oldInstallUninstaller = Join-Path $InstallDir "unins000.exe"
    if (Test-Path $oldInstallUninstaller) {{
        Invoke-CheckedProcess $oldInstallUninstaller @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART") "Previous uninstall"
    }}
    Remove-Item -LiteralPath $InstallDir -Recurse -Force -ErrorAction SilentlyContinue

    Write-CheckLog "Clean machine check started."
    Invoke-CheckedProcess $Installer @("/CURRENTUSER", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/DIR=$InstallDir", "/LOG=$(Join-Path $Root 'clean_install.log')") "Install"

    $Exe = Join-Path $InstallDir "TeamsCaptionTranslator.exe"
    $Uninstaller = Join-Path $InstallDir "unins000.exe"
    if (-not (Test-Path $Exe)) {{ throw "Installed exe missing: $Exe" }}
    if (-not (Test-Path $Uninstaller)) {{ throw "Uninstaller missing: $Uninstaller" }}

    $oldSmoke = $env:TCT_SMOKE
    $oldOcrSmoke = $env:TCT_PREPARE_OCR_SMOKE
    $oldFirstRunSmoke = $env:TCT_FIRST_RUN_SMOKE
    $oldDeepSeekSmoke = $env:TCT_DEEPSEEK_SMOKE
    $oldDeepSeekKey = $env:TCT_DEEPSEEK_API_KEY
    $oldAppData = $env:APPDATA
    try {{
        $env:APPDATA = $AppDataDir
        $env:TCT_SMOKE = "1"
        Invoke-CheckedProcess $Exe @() "App smoke"

        $env:TCT_SMOKE = $null
        $env:TCT_FIRST_RUN_SMOKE = "1"
        Invoke-CheckedProcess $Exe @() "First-run UI smoke"

        $env:TCT_FIRST_RUN_SMOKE = $null
        $env:TCT_PREPARE_OCR_SMOKE = "1"
        Invoke-CheckedProcess $Exe @() "OCR smoke"

        if ($DeepSeekApiKey.Trim()) {{
            $env:TCT_PREPARE_OCR_SMOKE = $null
            $env:TCT_DEEPSEEK_SMOKE = "1"
            $env:TCT_DEEPSEEK_API_KEY = $DeepSeekApiKey
            Invoke-CheckedProcess $Exe @() "DeepSeek smoke"
        }} else {{
            Write-CheckLog "DeepSeek smoke skipped because no DeepSeekApiKey was provided."
        }}
    }} finally {{
        $env:TCT_SMOKE = $oldSmoke
        $env:TCT_PREPARE_OCR_SMOKE = $oldOcrSmoke
        $env:TCT_FIRST_RUN_SMOKE = $oldFirstRunSmoke
        $env:TCT_DEEPSEEK_SMOKE = $oldDeepSeekSmoke
        $env:TCT_DEEPSEEK_API_KEY = $oldDeepSeekKey
        $env:APPDATA = $oldAppData
    }}

    Invoke-CheckedProcess $Uninstaller @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/LOG=$(Join-Path $Root 'clean_uninstall.log')") "Uninstall"
    if (Test-Path $InstallDir) {{ throw "Install directory still exists after uninstall: $InstallDir" }}

    "PASS" | Set-Content -Path $Result -Encoding UTF8
    Write-CheckLog "Clean machine check PASSED."
}} catch {{
    "FAIL: $($_.Exception.Message)" | Set-Content -Path $Result -Encoding UTF8
    Write-CheckLog "Clean machine check FAILED: $($_.Exception.Message)"
    throw
}}
"""


def build_release_manifest(version: str, installer_name: str, installer_sha256: str, installer_size: int) -> str:
    manifest = {
        "name": "Teams Caption Translator",
        "version": version,
        "package_platform": "windows",
        "recommended_zip": f"TeamsCaptionTranslator-v{version}-windows.zip",
        "compatibility_zip": f"TeamsCaptionTranslator-v{version}.zip",
        "installer": {
            "file": installer_name,
            "sha256": installer_sha256,
            "size_bytes": installer_size,
        },
        "ordinary_user_python_required": False,
        "bundled_ocr_models": ["craft_mlt_25k.pth", "japanese_g2.pth"],
        "config_locations": {
            "windows": "%APPDATA%\\TeamsCaptionTranslator",
            "macos": "~/Library/Application Support/TeamsCaptionTranslator",
        },
        "support_bundle": {
            "windows": "EXPORT_SUPPORT_BUNDLE.ps1",
            "macos": "EXPORT_MACOS_SUPPORT_BUNDLE.sh",
        },
        "validation": {
            "local_install_smoke": "run scripts\\verify_release.ps1 -OcrSmoke",
            "clean_windows": "run CLEAN_MACHINE_CHECK.ps1 on a clean Windows machine",
            "real_teams": "run MANUAL_TEAMS_CHECK.md in a real Teams rolling-caption session",
            "macos": "build and validate separately on a real Mac",
        },
        "macos_status": "scaffolded_not_validated",
    }
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--installer", default=str(root / "installer" / "TeamsCaptionTranslatorSetup-0.2.0.exe"))
    parser.add_argument("--version", default="0.2.0")
    args = parser.parse_args()

    installer = Path(args.installer).resolve()
    if not installer.exists():
        raise FileNotFoundError(f"Installer not found: {installer}")

    release_dir = root / "release" / f"TeamsCaptionTranslator-v{args.version}"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)

    release_installer = release_dir / installer.name
    shutil.copy2(installer, release_installer)

    digest = file_sha256(release_installer)
    size = release_installer.stat().st_size
    (release_dir / "SHA256.txt").write_text(
        "\n".join(
            [
                f"Teams Caption Translator v{args.version}",
                "",
                "File:",
                installer.name,
                "",
                "SHA256:",
                digest,
                "",
                "Size:",
                f"{size} bytes",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (release_dir / "START_HERE.txt").write_text(build_start_here(args.version, installer.name), encoding="utf-8")
    readme_cn = build_readme_cn(args.version, installer.name)
    (release_dir / "00_README_CN.txt").write_text(readme_cn, encoding="utf-8")
    (release_dir / "README_CN.txt").write_text(readme_cn, encoding="utf-8")
    (release_dir / "SEND_TO_TESTER.txt").write_text(build_send_to_tester(args.version, installer.name), encoding="utf-8")
    (release_dir / "QUICK_START.md").write_text(build_quick_start(args.version, installer.name), encoding="utf-8")
    (release_dir / "PLATFORM_SUPPORT.md").write_text(build_platform_support(args.version), encoding="utf-8")
    (release_dir / "MANUAL_TEAMS_CHECK.md").write_text(build_manual_teams_check(args.version, installer.name), encoding="utf-8")
    (release_dir / "CLEAN_MACHINE_CHECK.ps1").write_text(build_clean_machine_check(installer.name), encoding="utf-8")
    (release_dir / "EXPORT_SUPPORT_BUNDLE.ps1").write_text(build_support_bundle_exporter(), encoding="utf-8")
    (release_dir / "RELEASE_MANIFEST.json").write_text(
        build_release_manifest(args.version, installer.name, digest, size),
        encoding="utf-8",
    )

    zip_base = root / "release" / f"TeamsCaptionTranslator-v{args.version}"
    zip_path = Path(f"{zip_base}.zip")
    windows_zip_path = root / "release" / f"TeamsCaptionTranslator-v{args.version}-windows.zip"
    for path in (zip_path, windows_zip_path):
        if path.exists():
            path.unlink()
    shutil.make_archive(str(zip_base), "zip", root_dir=release_dir.parent, base_dir=release_dir.name)
    shutil.copy2(zip_path, windows_zip_path)

    print("Release package prepared:")
    print(f"  {release_dir}")
    print("Release zip:")
    print(f"  {zip_path}")
    print("Windows release zip:")
    print(f"  {windows_zip_path}")
    print("Installer SHA256:")
    print(f"  {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
