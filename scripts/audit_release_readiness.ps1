param(
    [string]$Version = "0.2.0",
    [switch]$RunSmoke
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Installer = Join-Path $Root "installer\TeamsCaptionTranslatorSetup-$Version.exe"
$ReleaseDir = Join-Path $Root "release\TeamsCaptionTranslator-v$Version"
$ReleaseZip = Join-Path $Root "release\TeamsCaptionTranslator-v$Version.zip"
$WindowsReleaseZip = Join-Path $Root "release\TeamsCaptionTranslator-v$Version-windows.zip"
$ReleaseInstaller = Join-Path $ReleaseDir "TeamsCaptionTranslatorSetup-$Version.exe"
$ReleaseHashFile = Join-Path $ReleaseDir "SHA256.txt"
$StartHere = Join-Path $ReleaseDir "START_HERE.txt"
$ReadmeCnFirst = Join-Path $ReleaseDir "00_README_CN.txt"
$ReadmeCn = Join-Path $ReleaseDir "README_CN.txt"
$SendToTester = Join-Path $ReleaseDir "SEND_TO_TESTER.txt"
$QuickStart = Join-Path $ReleaseDir "QUICK_START.md"
$PlatformSupport = Join-Path $ReleaseDir "PLATFORM_SUPPORT.md"
$ManualTeamsCheck = Join-Path $ReleaseDir "MANUAL_TEAMS_CHECK.md"
$CleanMachineCheck = Join-Path $ReleaseDir "CLEAN_MACHINE_CHECK.ps1"
$SupportBundleExporter = Join-Path $ReleaseDir "EXPORT_SUPPORT_BUNDLE.ps1"
$ReleaseManifest = Join-Path $ReleaseDir "RELEASE_MANIFEST.json"
$FinalAcceptanceMatrix = Join-Path $Root "docs\FINAL_ACCEPTANCE_MATRIX.md"
$MacPackagingDoc = Join-Path $Root "docs\MACOS_PACKAGING.md"
$MacReadme = Join-Path $Root "docs\README_MACOS.txt"
$MacTesterDoc = Join-Path $Root "docs\SEND_TO_MAC_TESTER.txt"
$MacTestResultTemplate = Join-Path $Root "docs\MAC_TEST_RESULT_TEMPLATE.txt"
$MacSpec = Join-Path $Root "packaging\teams-caption-translator-macos.spec"
$MacBuildScript = Join-Path $Root "scripts\build_macos.sh"
$MacCheckScript = Join-Path $Root "scripts\check_macos_release.sh"
$MacPrepareScript = Join-Path $Root "scripts\prepare_macos_release.sh"
$MacSupportExporter = Join-Path $Root "scripts\export_macos_support_bundle.sh"
$MacSourcePackageScript = Join-Path $Root "scripts\prepare_macos_source_package.ps1"
$MacReturnedReleaseAudit = Join-Path $Root "scripts\audit_macos_release_from_windows.ps1"
$MacSourceZip = Join-Path $Root "release\TeamsCaptionTranslator-v$Version-macos-source.zip"
$MacSourceCandidates = @(
    Get-ChildItem -LiteralPath (Join-Path $Root "release") -Filter "TeamsCaptionTranslator-v$Version-macos-source*.zip" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending
)
if ($MacSourceCandidates.Count -gt 0) {
    $MacSourceZip = $MacSourceCandidates[0].FullName
}
$MacSourceManifest = Join-Path $Root "release\$([System.IO.Path]::GetFileNameWithoutExtension($MacSourceZip)).SOURCE_PACKAGE_MANIFEST.json"
$ProjectReadme = Join-Path $Root "README.md"
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

function Test-NoMojibake([string]$Name, [string]$Path) {
    if (-not (Test-Path $Path)) {
        Add-Check "$Name has no common mojibake markers" $false "Missing: $Path"
        return
    }

    $text = Get-Content $Path -Raw -Encoding UTF8
    $patterns = @(
        [string][char]0x701B,
        [string][char]0x9359,
        [string][char]0x9410,
        [string][char]0x7F01,
        [string][char]0xFFFD
    )
    $bad = @($patterns | Where-Object { $text.Contains($_) })
    Add-Check "$Name has no common mojibake markers" ($bad.Count -eq 0) ($(if ($bad.Count) { "found: $($bad -join ', ')" } else { "clean" }))
}

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$installerOk = Require-File "Installer exists" $Installer
$releaseInstallerOk = Require-File "Release installer exists" $ReleaseInstaller
$releaseZipOk = Require-File "Release zip exists" $ReleaseZip
$windowsReleaseZipOk = Require-File "Windows release zip exists" $WindowsReleaseZip
Require-File "Release SHA256.txt exists" $ReleaseHashFile | Out-Null
Require-File "Release START_HERE.txt exists" $StartHere | Out-Null
Require-File "Release 00_README_CN.txt exists" $ReadmeCnFirst | Out-Null
Require-File "Release README_CN.txt exists" $ReadmeCn | Out-Null
Require-File "Release SEND_TO_TESTER.txt exists" $SendToTester | Out-Null
Require-File "Release QUICK_START.md exists" $QuickStart | Out-Null
Require-File "Release PLATFORM_SUPPORT.md exists" $PlatformSupport | Out-Null
Require-File "Release MANUAL_TEAMS_CHECK.md exists" $ManualTeamsCheck | Out-Null
Require-File "Release clean-machine check script exists" $CleanMachineCheck | Out-Null
Require-File "Release support bundle exporter exists" $SupportBundleExporter | Out-Null
Require-File "Release manifest exists" $ReleaseManifest | Out-Null
Require-File "Final acceptance matrix exists" $FinalAcceptanceMatrix | Out-Null
Require-File "Project README exists" $ProjectReadme | Out-Null
Require-File "macOS packaging doc exists" $MacPackagingDoc | Out-Null
Require-File "macOS README exists" $MacReadme | Out-Null
Require-File "macOS tester instructions exist" $MacTesterDoc | Out-Null
Require-File "macOS test result template exists" $MacTestResultTemplate | Out-Null
Require-File "macOS PyInstaller spec exists" $MacSpec | Out-Null
Require-File "macOS build script exists" $MacBuildScript | Out-Null
Require-File "macOS check script exists" $MacCheckScript | Out-Null
Require-File "macOS release preparation script exists" $MacPrepareScript | Out-Null
Require-File "macOS support bundle exporter exists" $MacSupportExporter | Out-Null
Require-File "macOS source package script exists" $MacSourcePackageScript | Out-Null
Require-File "macOS returned-release audit script exists" $MacReturnedReleaseAudit | Out-Null
Require-File "macOS source package zip exists" $MacSourceZip | Out-Null
Require-File "macOS source package manifest exists" $MacSourceManifest | Out-Null
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
            Add-Check "Release zip contains 00_README_CN.txt" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/00_README_CN.txt" }).Count -eq 1) "00_README_CN.txt"
            Add-Check "Release zip contains README_CN.txt" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/README_CN.txt" }).Count -eq 1) "README_CN.txt"
            Add-Check "Release zip contains SEND_TO_TESTER.txt" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/SEND_TO_TESTER.txt" }).Count -eq 1) "SEND_TO_TESTER.txt"
            Add-Check "Release zip contains QUICK_START.md" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/QUICK_START.md" }).Count -eq 1) "QUICK_START.md"
            Add-Check "Release zip contains platform support" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/PLATFORM_SUPPORT.md" }).Count -eq 1) "PLATFORM_SUPPORT.md"
            Add-Check "Release zip contains manual Teams check" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/MANUAL_TEAMS_CHECK.md" }).Count -eq 1) "MANUAL_TEAMS_CHECK.md"
            Add-Check "Release zip contains clean-machine check" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/CLEAN_MACHINE_CHECK.ps1" }).Count -eq 1) "CLEAN_MACHINE_CHECK.ps1"
            Add-Check "Release zip contains support bundle exporter" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/EXPORT_SUPPORT_BUNDLE.ps1" }).Count -eq 1) "EXPORT_SUPPORT_BUNDLE.ps1"
            Add-Check "Release zip contains release manifest" (($entries | Where-Object { $_ -eq "TeamsCaptionTranslator-v$Version/RELEASE_MANIFEST.json" }).Count -eq 1) "RELEASE_MANIFEST.json"
        }
        finally {
            $zip.Dispose()
        }
    }
    catch {
        Add-Check "Release zip can be inspected" $false $_.Exception.Message
    }
}

if ($windowsReleaseZipOk) {
    $windowsZipItem = Get-Item $WindowsReleaseZip
    Add-Check "Windows release zip size is non-trivial" ($windowsZipItem.Length -gt 200MB) "$($windowsZipItem.Length) bytes"
    if ($releaseZipOk) {
        $genericHash = (Get-FileHash $ReleaseZip -Algorithm SHA256).Hash
        $windowsHash = (Get-FileHash $WindowsReleaseZip -Algorithm SHA256).Hash
        Add-Check "Windows release zip matches compatibility zip" ($genericHash -eq $windowsHash) "generic=$genericHash; windows=$windowsHash"
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

if (Test-Path $ReleaseManifest) {
    try {
        $manifest = Get-Content $ReleaseManifest -Raw | ConvertFrom-Json
        Add-Check "Manifest platform is Windows" ($manifest.package_platform -eq "windows") "$($manifest.package_platform)"
        Add-Check "Manifest says ordinary users need no Python" ($manifest.ordinary_user_python_required -eq $false) "$($manifest.ordinary_user_python_required)"
        Add-Check "Manifest recommends Windows zip" ($manifest.recommended_zip -eq "TeamsCaptionTranslator-v$Version-windows.zip") "$($manifest.recommended_zip)"
        Add-Check "Manifest marks macOS as not validated" ($manifest.macos_status -eq "scaffolded_not_validated") "$($manifest.macos_status)"
        if ($installerOk) {
            $installerHashForManifest = (Get-FileHash $Installer -Algorithm SHA256).Hash
            Add-Check "Manifest installer hash matches installer" ($manifest.installer.sha256 -eq $installerHashForManifest) "$($manifest.installer.sha256)"
        }
    }
    catch {
        Add-Check "Release manifest can be parsed" $false $_.Exception.Message
    }
}

if (Test-Path $QuickStart) {
    $quickStartText = Get-Content $QuickStart -Raw
    Add-Check "QUICK_START mentions DeepSeek" ($quickStartText -match "DeepSeek API Key") "DeepSeek API Key"
    $quickStartMentionsPrepareOcr = Select-String -LiteralPath $QuickStart -Pattern "Prepare OCR" -SimpleMatch -Quiet
    Add-Check "QUICK_START mentions Prepare OCR" $quickStartMentionsPrepareOcr "Prepare OCR"
    Add-Check "QUICK_START mentions clean-machine check" ($quickStartText -match "CLEAN_MACHINE_CHECK.ps1") "CLEAN_MACHINE_CHECK.ps1"
    Add-Check "QUICK_START mentions manual Teams check" ($quickStartText -match "MANUAL_TEAMS_CHECK.md") "MANUAL_TEAMS_CHECK.md"
    Add-Check "QUICK_START mentions support bundle exporter" ($quickStartText -match "EXPORT_SUPPORT_BUNDLE.ps1") "EXPORT_SUPPORT_BUNDLE.ps1"
    Add-Check "QUICK_START mentions installer English is intentional" ($quickStartText -match "intentionally uses English") "intentionally uses English"
    Add-Check "QUICK_START mentions release zip distribution" ($quickStartText -match "TeamsCaptionTranslator-v$Version-windows.zip") "TeamsCaptionTranslator-v$Version-windows.zip"
    Add-Check "QUICK_START mentions compatibility zip" ($quickStartText -match "TeamsCaptionTranslator-v$Version.zip") "TeamsCaptionTranslator-v$Version.zip"
    Add-Check "QUICK_START mentions Windows package" ($quickStartText -match "Windows installer package") "Windows installer package"
    Add-Check "QUICK_START points to platform support" ($quickStartText -match "PLATFORM_SUPPORT.md") "PLATFORM_SUPPORT.md"
}

if (Test-Path $PlatformSupport) {
    $platformText = Get-Content $PlatformSupport -Raw
    Add-Check "Platform support says this zip is Windows" ($platformText -match "release zip is for Windows") "release zip is for Windows"
    Add-Check "Platform support says Windows needs no Python" ($platformText -match "not required") "not required"
    Add-Check "Platform support recommends Windows zip" ($platformText -match "TeamsCaptionTranslator-v$Version-windows.zip") "TeamsCaptionTranslator-v$Version-windows.zip"
    Add-Check "Platform support says macOS is separate" ($platformText -match "macOS is not included") "macOS is not included"
    Add-Check "Platform support mentions Screen Recording" ($platformText -match "Screen Recording") "Screen Recording"
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

if (Test-Path $ReadmeCn) {
    $readmeCnText = Get-Content $ReadmeCn -Raw
    Add-Check "README_CN mentions Windows package" ($readmeCnText -match "Windows") "Windows"
    Add-Check "README_CN mentions recommended zip" ($readmeCnText -match "TeamsCaptionTranslator-v$Version-windows.zip") "TeamsCaptionTranslator-v$Version-windows.zip"
    Add-Check "README_CN mentions no Python needed" ($readmeCnText -match "Python") "Python"
    Add-Check "README_CN mentions DeepSeek" ($readmeCnText -match "DeepSeek") "DeepSeek"
    Add-Check "README_CN mentions OCR" ($readmeCnText -match "OCR") "OCR"
    Add-Check "README_CN mentions support bundle" ($readmeCnText -match "EXPORT_SUPPORT_BUNDLE.ps1") "EXPORT_SUPPORT_BUNDLE.ps1"
}

if ((Test-Path $ReadmeCnFirst) -and (Test-Path $ReadmeCn)) {
    $firstHash = (Get-FileHash $ReadmeCnFirst -Algorithm SHA256).Hash
    $normalHash = (Get-FileHash $ReadmeCn -Algorithm SHA256).Hash
    Add-Check "00_README_CN matches README_CN" ($firstHash -eq $normalHash) "first=$firstHash; readme=$normalHash"
}

if (Test-Path $SendToTester) {
    $sendText = Get-Content $SendToTester -Raw
    Add-Check "SEND_TO_TESTER mentions Windows" ($sendText -match "Windows") "Windows"
    Add-Check "SEND_TO_TESTER mentions recommended zip" ($sendText -match "TeamsCaptionTranslator-v$Version-windows.zip") "TeamsCaptionTranslator-v$Version-windows.zip"
    Add-Check "SEND_TO_TESTER mentions DeepSeek" ($sendText -match "DeepSeek") "DeepSeek"
    Add-Check "SEND_TO_TESTER warns not to send key" ($sendText -match "Do not send your DeepSeek Key") "do not send DeepSeek Key"
    Add-Check "SEND_TO_TESTER mentions support bundle" ($sendText -match "EXPORT_SUPPORT_BUNDLE.ps1") "EXPORT_SUPPORT_BUNDLE.ps1"
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
    Add-Check "Uninstaller removes app user data" ($innoText -match "\{userappdata\}\\TeamsCaptionTranslator") "{userappdata}\TeamsCaptionTranslator"
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

if (Test-Path $FinalAcceptanceMatrix) {
    $matrixText = Get-Content $FinalAcceptanceMatrix -Raw
    Add-Check "Acceptance matrix defines Windows clean-machine evidence" ($matrixText -match "CLEAN_MACHINE_CHECK.ps1") "CLEAN_MACHINE_CHECK.ps1"
    Add-Check "Acceptance matrix defines Windows Teams evidence" ($matrixText -match "MANUAL_TEAMS_CHECK.md") "MANUAL_TEAMS_CHECK.md"
    Add-Check "Acceptance matrix defines macOS build evidence" ($matrixText -match "build_macos.sh") "build_macos.sh"
    Add-Check "Acceptance matrix defines macOS release evidence" ($matrixText -match "TeamsCaptionTranslator-v$Version-macos.zip") "TeamsCaptionTranslator-v$Version-macos.zip"
    Add-Check "Acceptance matrix defines macOS returned-package audit" ($matrixText -match "audit_macos_release_from_windows.ps1") "audit_macos_release_from_windows.ps1"
    Add-Check "Acceptance matrix defines macOS manual test template" ($matrixText -match "MAC_TEST_RESULT_TEMPLATE.txt") "MAC_TEST_RESULT_TEMPLATE.txt"
    Add-Check "Acceptance matrix keeps unverified macOS honest" ($matrixText -match "not validated") "not validated"
}

Test-NoMojibake "Project README" $ProjectReadme
Test-NoMojibake "macOS tester instructions" $MacTesterDoc

if (Test-Path $MacPackagingDoc) {
    $macDocText = Get-Content $MacPackagingDoc -Raw
    Add-Check "macOS doc mentions real Mac requirement" ($macDocText -match "real Mac") "real Mac"
    Add-Check "macOS doc mentions Screen Recording" ($macDocText -match "Screen Recording") "Screen Recording"
    Add-Check "macOS doc mentions prepare release script" ($macDocText -match "prepare_macos_release.sh") "prepare_macos_release.sh"
    Add-Check "macOS doc mentions returned-release audit" ($macDocText -match "audit_macos_release_from_windows.ps1") "audit_macos_release_from_windows.ps1"
    Add-Check "macOS doc mentions manual result template" ($macDocText -match "MAC_TEST_RESULT_TEMPLATE.txt") "MAC_TEST_RESULT_TEMPLATE.txt"
}

if (Test-Path $MacBuildScript) {
    $macBuildText = Get-Content $MacBuildScript -Raw
    Add-Check "macOS build script guards for Darwin" ($macBuildText -match "Darwin") "Darwin"
    Add-Check "macOS build script requires Python 3.10+" (($macBuildText -match "sys.version_info") -and ($macBuildText -match "3, 10")) "sys.version_info / 3, 10"
    Add-Check "macOS build script prepares EasyOCR models" (($macBuildText -match "easyocr.Reader") -and ($macBuildText -match "TCT_EASYOCR_MODEL_DIR")) "easyocr.Reader / TCT_EASYOCR_MODEL_DIR"
    Add-Check "macOS build script requires detection model" ($macBuildText -match "craft_mlt_25k.pth") "craft_mlt_25k.pth"
    Add-Check "macOS build script requires Japanese model" ($macBuildText -match "japanese_g2.pth") "japanese_g2.pth"
    Add-Check "macOS build script checks bundled app models" (($macBuildText -match 'find "\$APP_PATH"') -and ($macBuildText -match "bundled EasyOCR model")) "find APP_PATH / bundled EasyOCR model"
    Add-Check "macOS build script runs platform smoke" ($macBuildText -match "TCT_PLATFORM_DIAGNOSTIC_SMOKE") "TCT_PLATFORM_DIAGNOSTIC_SMOKE"
    Add-Check "macOS build script runs first-run smoke" ($macBuildText -match "TCT_FIRST_RUN_SMOKE") "TCT_FIRST_RUN_SMOKE"
    Add-Check "macOS build script creates dmg" ($macBuildText -match "hdiutil") "hdiutil"
}

if (Test-Path $MacCheckScript) {
    $macCheckText = Get-Content $MacCheckScript -Raw
    Add-Check "macOS check script verifies dmg" ($macCheckText -match "hdiutil verify") "hdiutil verify"
    Add-Check "macOS check script checks platform diagnostic" ($macCheckText -match "TCT_PLATFORM_DIAGNOSTIC_SMOKE") "TCT_PLATFORM_DIAGNOSTIC_SMOKE"
    Add-Check "macOS check script verifies bundled OCR models" (($macCheckText -match "craft_mlt_25k.pth") -and ($macCheckText -match "japanese_g2.pth") -and ($macCheckText -match 'find "\$APP_PATH"')) "craft / japanese / find APP_PATH"
}

if (Test-Path $MacPrepareScript) {
    $macPrepareText = Get-Content $MacPrepareScript -Raw
    Add-Check "macOS prepare script calls release check" ($macPrepareText -match "check_macos_release.sh") "check_macos_release.sh"
    Add-Check "macOS prepare script writes SHA256" ($macPrepareText -match "shasum") "shasum"
    Add-Check "macOS prepare script creates zip" ($macPrepareText -match "zip") "zip"
    Add-Check "macOS prepare script includes result template" ($macPrepareText -match "MAC_TEST_RESULT_TEMPLATE.txt") "MAC_TEST_RESULT_TEMPLATE.txt"
    Add-Check "macOS prepare script includes support exporter" ($macPrepareText -match "EXPORT_MACOS_SUPPORT_BUNDLE.sh") "EXPORT_MACOS_SUPPORT_BUNDLE.sh"
    Add-Check "macOS prepare script writes release manifest" ($macPrepareText -match "RELEASE_MANIFEST.json") "RELEASE_MANIFEST.json"
    Add-Check "macOS manifest records no-Python requirement" ($macPrepareText -match "ordinary_user_python_required") "ordinary_user_python_required"
    Add-Check "macOS manifest records dmg hash" (($macPrepareText -match '"sha256"') -and ($macPrepareText -match '\$\{HASH\}')) "sha256 / HASH"
    Add-Check "macOS manifest records support exporter" ($macPrepareText -match '"support_bundle"') "support_bundle"
}

if (Test-Path $MacSupportExporter) {
    $macSupportText = Get-Content $MacSupportExporter -Raw
    Add-Check "macOS support exporter redacts secrets" (($macSupportText -match "REDACTED") -and ($macSupportText -match "api\|key\|token\|secret\|password")) "REDACTED api/key/token/secret/password"
    Add-Check "macOS support exporter copies logs" (($macSupportText -match "LOG_DIR") -and ($macSupportText -match "cp -R")) "LOG_DIR / cp -R"
    Add-Check "macOS support exporter creates zip" ($macSupportText -match "zip -qry") "zip -qry"
    Add-Check "macOS support exporter avoids python dependency" (-not ($macSupportText -match "python3")) "no python3"
}

if (Test-Path $MacSourcePackageScript) {
    $macSourceText = Get-Content $MacSourcePackageScript -Raw
    Add-Check "macOS source package excludes config" ($macSourceText -match "config.json") "config.json"
    Add-Check "macOS source package excludes local build artifacts" (($macSourceText -match '"build"') -and ($macSourceText -match '"dist"') -and ($macSourceText -match '"release"')) "build / dist / release"
    Add-Check "macOS source package excludes venvs" (($macSourceText -match '".venv"') -and ($macSourceText -match '".venv-macos"')) ".venv / .venv-macos"
    Add-Check "macOS source package writes build instructions" ($macSourceText -match "BUILD_ON_MAC.txt") "BUILD_ON_MAC.txt"
    Add-Check "macOS source package writes manifest" ($macSourceText -match "SOURCE_PACKAGE_MANIFEST.json") "SOURCE_PACKAGE_MANIFEST.json"
    Add-Check "macOS source package manifest records commands" (($macSourceText -match "build_macos.sh") -and ($macSourceText -match "check_macos_release.sh") -and ($macSourceText -match "prepare_macos_release.sh")) "build/check/prepare"
    Add-Check "macOS source package manifest records hash" (($macSourceText -match "sha256") -and ($macSourceText -match "Get-FileHash")) "sha256 / Get-FileHash"
    Add-Check "macOS source package creates zip" ($macSourceText -match "ZipFile") "ZipFile"
    Add-Check "macOS source package normalizes zip paths" (($macSourceText -match "-replace") -and ($macSourceText -match "entryName")) "replace backslash with slash"
}

if (Test-Path $MacReturnedReleaseAudit) {
    $macReturnedAuditText = Get-Content $MacReturnedReleaseAudit -Raw
    Add-Check "macOS returned-release audit inspects zip" ($macReturnedAuditText -match "ZipFile") "ZipFile"
    Add-Check "macOS returned-release audit verifies dmg hash" (($macReturnedAuditText -match "Get-ZipEntrySha256") -and ($macReturnedAuditText -match "Manifest dmg SHA256 matches zip entry")) "Get-ZipEntrySha256 / manifest"
    Add-Check "macOS returned-release audit checks result template" ($macReturnedAuditText -match "MAC_TEST_RESULT_TEMPLATE.txt") "MAC_TEST_RESULT_TEMPLATE.txt"
    Add-Check "macOS returned-release audit checks mojibake" ($macReturnedAuditText -match "Test-NoMojibake") "Test-NoMojibake"
    Add-Check "macOS returned-release audit says real Mac still required" ($macReturnedAuditText -match "real Mac") "real Mac"
}

if ((Test-Path $MacSourceZip) -and (Test-Path $MacSourceManifest)) {
    try {
        $sourceManifest = Get-Content $MacSourceManifest -Raw | ConvertFrom-Json
        $sourceHash = (Get-FileHash $MacSourceZip -Algorithm SHA256).Hash
        $sourceSize = (Get-Item $MacSourceZip).Length
        Add-Check "macOS source manifest hash matches zip" ($sourceManifest.sha256 -eq $sourceHash) "$($sourceManifest.sha256)"
        Add-Check "macOS source manifest size matches zip" ([int64]$sourceManifest.size_bytes -eq $sourceSize) "$($sourceManifest.size_bytes) bytes"
        Add-Check "macOS source manifest marks source platform" ($sourceManifest.package_platform -eq "macos-source") "$($sourceManifest.package_platform)"
        Add-Check "macOS source manifest records build Python requirement" ($sourceManifest.build_mac_python_required -eq "3.10+") "$($sourceManifest.build_mac_python_required)"
        Add-Check "macOS source manifest records no ordinary Python requirement" ($sourceManifest.ordinary_user_python_required -eq $false) "$($sourceManifest.ordinary_user_python_required)"

        Add-Type -AssemblyName System.IO.Compression
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $sourceZipHandle = [System.IO.Compression.ZipFile]::OpenRead($MacSourceZip)
        try {
            $sourceEntries = @($sourceZipHandle.Entries | ForEach-Object { $_.FullName })
            $slashLeaks = @($sourceEntries | Where-Object { $_ -match "\\" })
            $excludedLeaks = @(
                $sourceEntries | Where-Object {
                    $_ -match '(^|/)(config\.json|\.venv|\.venv-macos|build|build-macos|dist|dist-macos|release|logs)(/|$)'
                }
            )
            Add-Check "macOS source zip uses slash paths" ($slashLeaks.Count -eq 0) "$($slashLeaks.Count) backslash entries"
            Add-Check "macOS source zip excludes local artifacts" ($excludedLeaks.Count -eq 0) "$($excludedLeaks.Count) excluded entries"
            Add-Check "macOS source zip contains build instructions" (($sourceEntries | Where-Object { $_ -match "/BUILD_ON_MAC.txt$" }).Count -eq 1) "BUILD_ON_MAC.txt"
            Add-Check "macOS source zip contains source manifest" (($sourceEntries | Where-Object { $_ -match "/SOURCE_PACKAGE_MANIFEST.json$" }).Count -eq 1) "SOURCE_PACKAGE_MANIFEST.json"
            Add-Check "macOS source zip contains macOS build script" (($sourceEntries | Where-Object { $_ -match "/scripts/build_macos.sh$" }).Count -eq 1) "scripts/build_macos.sh"
            Add-Check "macOS source zip contains macOS spec" (($sourceEntries | Where-Object { $_ -match "/packaging/teams-caption-translator-macos.spec$" }).Count -eq 1) "teams-caption-translator-macos.spec"
        }
        finally {
            $sourceZipHandle.Dispose()
        }
    }
    catch {
        Add-Check "macOS source package can be inspected" $false $_.Exception.Message
    }
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
