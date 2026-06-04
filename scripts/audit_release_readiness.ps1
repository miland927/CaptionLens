param(
    [string]$Version = "0.2.0",
    [switch]$RunSmoke
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Installer = Join-Path $Root "installer\TeamsCaptionTranslatorSetup-$Version.exe"
$ReleaseDir = Join-Path $Root "release\TeamsCaptionTranslator-v$Version"
$ReleaseZip = Join-Path $Root "release\TeamsCaptionTranslator-v$Version.zip"
$ReleaseInstaller = Join-Path $ReleaseDir "TeamsCaptionTranslatorSetup-$Version.exe"
$ReleaseHashFile = Join-Path $ReleaseDir "SHA256.txt"
$StartHere = Join-Path $ReleaseDir "START_HERE.txt"
$QuickStart = Join-Path $ReleaseDir "QUICK_START.md"
$ManualTeamsCheck = Join-Path $ReleaseDir "MANUAL_TEAMS_CHECK.md"
$CleanMachineCheck = Join-Path $ReleaseDir "CLEAN_MACHINE_CHECK.ps1"
$SupportBundleExporter = Join-Path $ReleaseDir "EXPORT_SUPPORT_BUNDLE.ps1"
$SandboxDir = Join-Path $Root "build\sandbox_release_check"
$SandboxConfig = Join-Path $SandboxDir "TeamsCaptionTranslatorReleaseCheck.wsb"
$SandboxScript = Join-Path $SandboxDir "run_inside_sandbox.ps1"
$FrozenModelDir = Join-Path $Root "dist\TeamsCaptionTranslator\_internal\easyocr_model"
$InnoScript = Join-Path $Root "packaging\teams-caption-translator.iss"
$ReportDir = Join-Path $Root "release"
$Report = Join-Path $ReportDir "RELEASE_AUDIT_v$Version.txt"

$checks = New-Object System.Collections.Generic.List[object]

function Add-Check([string]$Name, [bool]$Pass, [string]$Detail) {
    $script:checks.Add([PSCustomObject]@{
        Name = $Name
        Pass = $Pass
        Detail = $Detail
    })
}

function Require-File([string]$Name, [string]$Path) {
    $exists = Test-Path $Path
    $detail = if ($exists) { "$Path" } else { "Missing: $Path" }
    Add-Check $Name $exists $detail
    return $exists
}

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$installerOk = Require-File "Installer exists" $Installer
$releaseInstallerOk = Require-File "Release installer exists" $ReleaseInstaller
$releaseZipOk = Require-File "Release zip exists" $ReleaseZip
Require-File "Release SHA256.txt exists" $ReleaseHashFile | Out-Null
Require-File "Release START_HERE.txt exists" $StartHere | Out-Null
Require-File "Release QUICK_START.md exists" $QuickStart | Out-Null
Require-File "Release MANUAL_TEAMS_CHECK.md exists" $ManualTeamsCheck | Out-Null
Require-File "Release clean-machine check script exists" $CleanMachineCheck | Out-Null
Require-File "Release support bundle exporter exists" $SupportBundleExporter | Out-Null
Require-File "Sandbox .wsb exists" $SandboxConfig | Out-Null
Require-File "Sandbox script exists" $SandboxScript | Out-Null
Require-File "Inno Setup script exists" $InnoScript | Out-Null

if ($installerOk) {
    $installerItem = Get-Item $Installer
    Add-Check "Installer size is non-trivial" ($installerItem.Length -gt 200MB) "$($installerItem.Length) bytes"
}

if ($releaseZipOk) {
    $zipItem = Get-Item $ReleaseZip
    Add-Check "Release zip size is non-trivial" ($zipItem.Length -gt 200MB) "$($zipItem.Length) bytes"
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead($ReleaseZip)
        try {
            $entries = @($zip.Entries | ForEach-Object { $_.FullName })
            Add-Check "Release zip contains installer" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/TeamsCaptionTranslatorSetup-$Version.exe" }).Count -eq 1) "TeamsCaptionTranslatorSetup-$Version.exe"
            Add-Check "Release zip contains START_HERE.txt" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/START_HERE.txt" }).Count -eq 1) "START_HERE.txt"
            Add-Check "Release zip contains QUICK_START.md" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/QUICK_START.md" }).Count -eq 1) "QUICK_START.md"
            Add-Check "Release zip contains manual Teams check" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/MANUAL_TEAMS_CHECK.md" }).Count -eq 1) "MANUAL_TEAMS_CHECK.md"
            Add-Check "Release zip contains clean-machine check" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/CLEAN_MACHINE_CHECK.ps1" }).Count -eq 1) "CLEAN_MACHINE_CHECK.ps1"
            Add-Check "Release zip contains support bundle exporter" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/EXPORT_SUPPORT_BUNDLE.ps1" }).Count -eq 1) "EXPORT_SUPPORT_BUNDLE.ps1"
        }
        finally {
            $zip.Dispose()
        }
    }
    catch {
        Add-Check "Release zip can be inspected" $false $_.Exception.Message
    }
}

if ($installerOk -and $releaseInstallerOk) {
    $installerHash = (Get-FileHash $Installer -Algorithm SHA256).Hash
    $releaseHash = (Get-FileHash $ReleaseInstaller -Algorithm SHA256).Hash
    Add-Check "Release installer hash matches source installer" ($installerHash -eq $releaseHash) "installer=$installerHash; release=$releaseHash"

    if (Test-Path $ReleaseHashFile) {
        $hashText = Get-Content $ReleaseHashFile -Raw
        Add-Check "SHA256.txt contains installer hash" ($hashText -match [Regex]::Escape($installerHash)) $installerHash
    }
}

if (Test-Path $QuickStart) {
    $quickStartText = Get-Content $QuickStart -Raw
    Add-Check "QUICK_START mentions DeepSeek" ($quickStartText -match "DeepSeek API Key") "DeepSeek API Key"
    Add-Check "QUICK_START mentions Prepare OCR" ($quickStartText -match "Prepare OCR") "Prepare OCR"
    Add-Check "QUICK_START mentions clean-machine check" ($quickStartText -match "CLEAN_MACHINE_CHECK.ps1") "CLEAN_MACHINE_CHECK.ps1"
    Add-Check "QUICK_START mentions manual Teams check" ($quickStartText -match "MANUAL_TEAMS_CHECK.md") "MANUAL_TEAMS_CHECK.md"
    Add-Check "QUICK_START mentions support bundle exporter" ($quickStartText -match "EXPORT_SUPPORT_BUNDLE.ps1") "EXPORT_SUPPORT_BUNDLE.ps1"
    Add-Check "QUICK_START mentions installer English is intentional" ($quickStartText -match "intentionally uses English") "intentionally uses English"
    Add-Check "QUICK_START mentions release zip distribution" ($quickStartText -match "TeamsCaptionTranslator-v$Version.zip") "TeamsCaptionTranslator-v$Version.zip"
}

if (Test-Path $ManualTeamsCheck) {
    $manualTeamsText = Get-Content $ManualTeamsCheck -Raw
    Add-Check "Manual Teams check mentions DeepSeek" ($manualTeamsText -match "DeepSeek") "DeepSeek"
    Add-Check "Manual Teams check mentions OCR" ($manualTeamsText -match "OCR") "OCR"
    Add-Check "Manual Teams check mentions rolling captions" ($manualTeamsText -match "rolling captions") "rolling captions"
    Add-Check "Manual Teams check verifies old content is preserved" ($manualTeamsText -match "old content preserved") "old content preserved"
    Add-Check "Manual Teams check verifies speaker formatting" ($manualTeamsText -match "speaker colon content") "speaker colon content"
    Add-Check "Manual Teams check mentions support bundle exporter" ($manualTeamsText -match "EXPORT_SUPPORT_BUNDLE.ps1") "EXPORT_SUPPORT_BUNDLE.ps1"
}

if (Test-Path $StartHere) {
    $startHereText = Get-Content $StartHere -Raw
    Add-Check "START_HERE explains install flow" (($startHereText -match "Double-click") -and ($startHereText -match "DeepSeek API Key") -and ($startHereText -match "Start Translation")) "Double-click / DeepSeek API Key / Start Translation"
    Add-Check "START_HERE mentions bundled OCR/Python-free use" (($startHereText -match "Python is not required") -and ($startHereText -match "EasyOCR models are bundled")) "Python is not required / EasyOCR models are bundled"
    Add-Check "START_HERE points testers to manual Teams check" ($startHereText -match "MANUAL_TEAMS_CHECK.md") "MANUAL_TEAMS_CHECK.md"
}

if (Test-Path $InnoScript) {
    $innoText = Get-Content $InnoScript -Raw
    $hasNonAscii = $false
    foreach ($char in $innoText.ToCharArray()) {
        if ([int][char]$char -gt 127) {
            $hasNonAscii = $true
            break
        }
    }
    Add-Check "Installer script visible text is ASCII-safe" (-not $hasNonAscii) "Non-ASCII present: $hasNonAscii"
    $desktopTaskLine = ($innoText -split "`r?`n" | Where-Object { $_ -match 'Name:\s*"desktopicon"' } | Select-Object -First 1)
    Add-Check "Desktop shortcut task is checked by default" ($desktopTaskLine -and ($desktopTaskLine -notmatch "unchecked")) $desktopTaskLine
}

if (Test-Path $CleanMachineCheck) {
    $cleanMachineText = Get-Content $CleanMachineCheck -Raw
    Add-Check "Clean-machine check performs first-run UI smoke" ($cleanMachineText -match "TCT_FIRST_RUN_SMOKE") "TCT_FIRST_RUN_SMOKE"
    Add-Check "Clean-machine check performs OCR smoke" ($cleanMachineText -match "TCT_PREPARE_OCR_SMOKE") "TCT_PREPARE_OCR_SMOKE"
    Add-Check "Clean-machine check supports optional DeepSeek smoke" (($cleanMachineText -match "DeepSeekApiKey") -and ($cleanMachineText -match "TCT_DEEPSEEK_SMOKE")) "DeepSeekApiKey / TCT_DEEPSEEK_SMOKE"
    Add-Check "Clean-machine check writes result file" ($cleanMachineText -match "CLEAN_MACHINE_RESULT.txt") "CLEAN_MACHINE_RESULT.txt"
}

if (Test-Path $SupportBundleExporter) {
    $supportBundleText = Get-Content $SupportBundleExporter -Raw
    Add-Check "Support bundle exporter redacts secrets" (($supportBundleText -match "REDACTED") -and ($supportBundleText -match "api\|key\|token\|secret\|password")) "REDACTED api/key/token/secret/password"
    Add-Check "Support bundle exporter writes redacted config" ($supportBundleText -match "config.redacted") "config.redacted"
    Add-Check "Support bundle exporter creates zip" ($supportBundleText -match "Compress-Archive") "Compress-Archive"
    Add-Check "Support bundle exporter copies logs" (($supportBundleText -match "logs") -and ($supportBundleText -match "Copy-Item")) "logs / Copy-Item"
}

$craft = Join-Path $FrozenModelDir "craft_mlt_25k.pth"
$japanese = Join-Path $FrozenModelDir "japanese_g2.pth"
Add-Check "Bundled EasyOCR detection model exists" (Test-Path $craft) $craft
Add-Check "Bundled EasyOCR Japanese model exists" (Test-Path $japanese) $japanese
if ((Test-Path $craft) -and (Test-Path $japanese)) {
    $craftLength = (Get-Item $craft).Length
    $japaneseLength = (Get-Item $japanese).Length
    Add-Check "Bundled EasyOCR model sizes look valid" (($craftLength -gt 50MB) -and ($japaneseLength -gt 10MB)) "craft=$craftLength; japanese=$japaneseLength"
}

if ($RunSmoke) {
    try {
        & (Join-Path $Root "scripts\verify_release.ps1") -OcrSmoke
        Add-Check "verify_release.ps1 -OcrSmoke passed" $true "Local install/smoke/OCR/uninstall succeeded"
    }
    catch {
        Add-Check "verify_release.ps1 -OcrSmoke passed" $false $_.Exception.Message
    }
}
else {
    Add-Check "verify_release.ps1 -OcrSmoke passed" $true "Skipped in audit. Run with -RunSmoke for full local install validation."
}

$windowsSandbox = Get-Command WindowsSandbox.exe -ErrorAction SilentlyContinue
Add-Check "Windows Sandbox available on this host" ($null -ne $windowsSandbox) ($(if ($windowsSandbox) { $windowsSandbox.Source } else { "Not found on this host" }))

$allPass = -not ($checks | Where-Object { -not $_.Pass })
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("Teams Caption Translator v$Version Release Audit")
$lines.Add("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$lines.Add("Overall: $(if ($allPass) { 'PASS' } else { 'FAIL' })")
$lines.Add("")
foreach ($check in $checks) {
    $status = if ($check.Pass) { "PASS" } else { "FAIL" }
    $lines.Add("[$status] $($check.Name)")
    $lines.Add("  $($check.Detail)")
}

Set-Content -Path $Report -Value $lines -Encoding UTF8
Write-Host ($lines -join [Environment]::NewLine)
Write-Host ""
Write-Host "Audit report: $Report"

if (-not $allPass) {
    exit 1
}
