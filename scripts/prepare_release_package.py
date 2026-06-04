from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def build_quick_start(version: str, installer_name: str) -> str:
    return f"""# Teams 字幕翻译器 v{version} 快速使用

## 分发

如果你是把工具发给别人，推荐发送 `TeamsCaptionTranslator-v{version}.zip`。对方解压后双击里面的 `{installer_name}` 即可。

## 安装

双击：

```text
{installer_name}
```

安装向导会显示英文，这是为了避免不同 Windows 编码环境下出现乱码。安装完成后程序会自动启动，也可以从桌面图标或开始菜单打开 "Teams Caption Translator"。

## 第一次使用

1. 输入 DeepSeek API Key。
2. 点击“保存设置”。
3. 点击“测试 DeepSeek”，确认 Key 和网络可用。
4. 点击“准备 OCR”，确认 OCR 就绪。
5. 打开 Microsoft Teams 字幕。
6. 点击“选择区域”，框住 Teams 字幕滚动区域。
7. 点击“测试 OCR”，确认能识别原文。
8. 点击“开始翻译”。

## OCR 说明

安装包已内置日语 EasyOCR 模型。普通用户不需要安装 Python，也不需要手动下载 OCR 模型。

## 最终验收

如果要确认它真的适合发给别人，请看 `MANUAL_TEAMS_CHECK.md`。自动脚本能检查安装、启动、OCR 和 DeepSeek API；真实 Teams 滚动字幕仍建议人工跑一次。

## 日志位置

如果程序没有正常启动或无法识别字幕，查看：

```text
%APPDATA%\\TeamsCaptionTranslator\\logs
```

也可以在 release 文件夹里运行 `EXPORT_SUPPORT_BUNDLE.ps1`，它会生成一个脱敏诊断包，方便发给维护者排查，不会包含明文 DeepSeek Key。

---

# Teams Caption Translator v{version} Quick Start

## Distribution

If you are sending this tool to someone else, send `TeamsCaptionTranslator-v{version}.zip`. They can unzip it and double-click `{installer_name}`.

## Install

Double-click:

```text
{installer_name}
```

The installer wizard intentionally uses English to avoid text-encoding issues on different Windows machines. After installation, the app launches automatically. You can also open "Teams Caption Translator" from the desktop shortcut or Start Menu.

## First Run

1. Enter your DeepSeek API Key.
2. Click "Save Settings".
3. Click "Test DeepSeek" to verify the key and network.
4. Click "Prepare OCR" to initialize OCR.
5. Open Microsoft Teams captions.
6. Click "Select Region" and drag around the scrolling caption area.
7. Click "Test OCR" and confirm the original text appears.
8. Click "Start Translation".

## OCR Notes

The installer bundles the Japanese EasyOCR models. Users do not need to install Python or manually download OCR models.

## Final Acceptance

Before distributing broadly, use `MANUAL_TEAMS_CHECK.md`. The automated script verifies install, startup, OCR, and DeepSeek API access; a real Teams rolling-caption session should still be checked manually once.

## Logs

If the app does not start or OCR does not work, check:

```text
%APPDATA%\\TeamsCaptionTranslator\\logs
```

You can also run `EXPORT_SUPPORT_BUNDLE.ps1` from this release folder. It creates a redacted diagnostics zip for maintainers and does not include the plain DeepSeek API key.

## Clean Machine Check

On a test Windows machine, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\\CLEAN_MACHINE_CHECK.ps1
```

The script installs this package, runs app and OCR smoke tests, uninstalls it, and writes `CLEAN_MACHINE_RESULT.txt`.

To also verify DeepSeek on the test machine, pass a key:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\\CLEAN_MACHINE_CHECK.ps1 -DeepSeekApiKey "sk-..."
```
"""


def build_start_here(version: str, installer_name: str) -> str:
    return f"""START HERE - Teams Caption Translator v{version}

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
- If something does not work, open QUICK_START.md or check:
  %APPDATA%\\TeamsCaptionTranslator\\logs
- To collect safe diagnostics, run EXPORT_SUPPORT_BUNDLE.ps1.

For testers:

Run CLEAN_MACHINE_CHECK.ps1 to verify install, first-run UI, OCR, and uninstall.
To also test DeepSeek, run:

powershell -NoProfile -ExecutionPolicy Bypass -File .\\CLEAN_MACHINE_CHECK.ps1 -DeepSeekApiKey "sk-..."

Then run the real Teams check in MANUAL_TEAMS_CHECK.md once before broad distribution.
"""


def build_manual_teams_check(version: str, installer_name: str) -> str:
    return f"""# Teams 字幕翻译器 v{version} 人工验收清单

这个清单用于最后确认“普通用户双击安装，输入 DeepSeek Key，就能使用”的目标。自动脚本已经能测安装、启动、OCR 初始化和 DeepSeek API；真实 Teams 滚动字幕仍建议人工跑一次。

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
3. 从自动启动窗口、桌面快捷方式，或开始菜单打开 `Teams Caption Translator`。
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

## 记录结果

```text
测试日期:
Windows 版本:
Teams 版本:
是否干净环境:
CLEAN_MACHINE_RESULT.txt:
DeepSeek smoke:
OCR 引擎:
真实 Teams 字幕是否通过:
备注:
```

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
    if ($null -eq $Value) {
        return $null
    }
    if ($Value -is [System.Collections.IDictionary]) {
        $result = [ordered]@{}
        foreach ($key in $Value.Keys) {
            if ([string]$key -match '(?i)(api|key|token|secret|password)') {
                $result[$key] = "***REDACTED***"
            }
            else {
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
            }
            else {
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
}
catch {
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
    }
    catch {
        "Log directory existed, but could not be copied: $($_.Exception.Message)" | Set-Content -Path (Join-Path $WorkDir "logs.copy_failed.txt") -Encoding UTF8
    }
}

if (Test-Path $ConfigPath) {
    try {
        $config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $redacted = Redact-Object $config
        $redacted | ConvertTo-Json -Depth 20 | Set-Content -Path (Join-Path $WorkDir "config.redacted.json") -Encoding UTF8
    }
    catch {
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

function Quote-ProcessArgument([string]$Argument) {{
    if ($Argument -match '[\\s"]') {{
        return '"' + ($Argument -replace '"', '\\\"') + '"'
    }}
    return $Argument
}}

function Invoke-CheckedProcess([string]$FilePath, [string[]]$Arguments, [string]$Label) {{
    $argumentLine = ($Arguments | ForEach-Object {{ Quote-ProcessArgument $_ }}) -join " "
    Write-CheckLog "${{Label}}: $FilePath $argumentLine"
    $startArgs = @{{
        FilePath = $FilePath
        Wait = $true
        PassThru = $true
        WindowStyle = "Hidden"
    }}
    if ($argumentLine.Trim()) {{
        $startArgs.ArgumentList = $argumentLine
    }}
    $process = Start-Process @startArgs
    Write-CheckLog "$Label exit code: $($process.ExitCode)"
    if ($process.ExitCode -ne 0) {{
        throw "$Label failed with code $($process.ExitCode)"
    }}
}}

try {{
    Remove-Item -LiteralPath $Result -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $Log -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $AppDataDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $AppDataDir | Out-Null

    if (-not (Test-Path $Installer)) {{
        throw "Installer not found: $Installer"
    }}

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
        $env:TCT_PREPARE_OCR_SMOKE = $null
        $env:TCT_FIRST_RUN_SMOKE = $null
        $env:TCT_DEEPSEEK_SMOKE = $null
        $env:TCT_DEEPSEEK_API_KEY = $null
        Invoke-CheckedProcess $Exe @() "App smoke"

        $env:TCT_SMOKE = $null
        $env:TCT_PREPARE_OCR_SMOKE = $null
        $env:TCT_FIRST_RUN_SMOKE = "1"
        Invoke-CheckedProcess $Exe @() "First-run UI smoke"

        $env:TCT_FIRST_RUN_SMOKE = $null
        $env:TCT_PREPARE_OCR_SMOKE = "1"
        Invoke-CheckedProcess $Exe @() "OCR smoke"

        if ($DeepSeekApiKey.Trim()) {{
            $env:TCT_PREPARE_OCR_SMOKE = $null
            $env:TCT_FIRST_RUN_SMOKE = $null
            $env:TCT_DEEPSEEK_SMOKE = "1"
            $env:TCT_DEEPSEEK_API_KEY = $DeepSeekApiKey
            Invoke-CheckedProcess $Exe @() "DeepSeek smoke"
        }}
        else {{
            Write-CheckLog "DeepSeek smoke skipped because no DeepSeekApiKey was provided."
        }}
    }}
    finally {{
        $env:TCT_SMOKE = $oldSmoke
        $env:TCT_PREPARE_OCR_SMOKE = $oldOcrSmoke
        $env:TCT_FIRST_RUN_SMOKE = $oldFirstRunSmoke
        $env:TCT_DEEPSEEK_SMOKE = $oldDeepSeekSmoke
        $env:TCT_DEEPSEEK_API_KEY = $oldDeepSeekKey
        $env:APPDATA = $oldAppData
    }}

    $AppLog = Join-Path $AppDataDir "TeamsCaptionTranslator\\logs\\app.log"
    if (Test-Path $AppLog) {{
        Copy-Item -LiteralPath $AppLog -Destination (Join-Path $Root "clean_app.log") -Force
    }}

    Invoke-CheckedProcess $Uninstaller @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/LOG=$(Join-Path $Root 'clean_uninstall.log')") "Uninstall"
    if (Test-Path $InstallDir) {{ throw "Install directory still exists after uninstall: $InstallDir" }}

    "PASS" | Set-Content -Path $Result -Encoding UTF8
    Write-CheckLog "Clean machine check PASSED."
}}
catch {{
    "FAIL: $($_.Exception.Message)" | Set-Content -Path $Result -Encoding UTF8
    Write-CheckLog "Clean machine check FAILED: $($_.Exception.Message)"
    throw
}}
"""


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
    (release_dir / "QUICK_START.md").write_text(build_quick_start(args.version, installer.name), encoding="utf-8")
    (release_dir / "MANUAL_TEAMS_CHECK.md").write_text(
        build_manual_teams_check(args.version, installer.name),
        encoding="utf-8",
    )
    (release_dir / "CLEAN_MACHINE_CHECK.ps1").write_text(build_clean_machine_check(installer.name), encoding="utf-8")
    (release_dir / "EXPORT_SUPPORT_BUNDLE.ps1").write_text(build_support_bundle_exporter(), encoding="utf-8")

    zip_base = root / "release" / f"TeamsCaptionTranslator-v{args.version}"
    zip_path = Path(f"{zip_base}.zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_base), "zip", root_dir=release_dir.parent, base_dir=release_dir.name)

    print("Release package prepared:")
    print(f"  {release_dir}")
    print("Release zip:")
    print(f"  {zip_path}")
    print("Installer SHA256:")
    print(f"  {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
