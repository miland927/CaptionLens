param(
    [string]$InstallerPath = "",
    [string]$InstallDir = "",
    [switch]$OcrSmoke,
    [switch]$KeepInstall
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$BuildDir = Join-Path $Root "build"
$DefaultInstaller = Join-Path $Root "installer\TeamsCaptionTranslatorSetup-0.2.0.exe"
$DefaultInstallDir = Join-Path $BuildDir "release_check_install"
$ReleaseLogDir = Join-Path $BuildDir "release_check_logs"
$AppDataDir = Join-Path $BuildDir "release_check_appdata"
$InstallLog = Join-Path $ReleaseLogDir "install.log"
$UninstallLog = Join-Path $ReleaseLogDir "uninstall.log"

if (-not $InstallerPath) {
    $InstallerPath = $DefaultInstaller
}
if (-not $InstallDir) {
    $InstallDir = $DefaultInstallDir
}

$InstallerPath = [System.IO.Path]::GetFullPath($InstallerPath)
$InstallDir = [System.IO.Path]::GetFullPath($InstallDir)
$BuildDirFull = [System.IO.Path]::GetFullPath($BuildDir)

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "== $Message =="
}

function Assert-Exists([string]$Path, [string]$Message) {
    if (-not (Test-Path $Path)) {
        throw "$Message`: $Path"
    }
}

function Assert-UnderBuildDir([string]$Path, [string]$Label) {
    $full = [System.IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($BuildDirFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label must stay under build directory for release verification: $full"
    }
}

function Quote-ProcessArgument([string]$Argument) {
    if ($Argument -match '[\s"]') {
        return '"' + ($Argument -replace '"', '\"') + '"'
    }
    return $Argument
}

function Invoke-CheckedProcess([string]$FilePath, [string[]]$Arguments, [string]$Label) {
    $argumentLine = ($Arguments | ForEach-Object { Quote-ProcessArgument $_ }) -join " "
    $process = Start-Process -FilePath $FilePath -ArgumentList $argumentLine -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -ne 0) {
        throw "$Label failed with code $($process.ExitCode)"
    }
}

Write-Step "Checking release inputs"
Assert-Exists $InstallerPath "Installer not found"
Assert-UnderBuildDir $InstallDir "InstallDir"
Assert-UnderBuildDir $ReleaseLogDir "ReleaseLogDir"
Assert-UnderBuildDir $AppDataDir "AppDataDir"

New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
if (Test-Path $InstallDir) {
    $ExistingUninstaller = Join-Path $InstallDir "unins000.exe"
    if (Test-Path $ExistingUninstaller) {
        Write-Step "Removing previous release-check install"
        Invoke-CheckedProcess $ExistingUninstaller @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART") "Previous release-check uninstall"
    }
    Remove-Item -LiteralPath $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
}
Remove-Item -LiteralPath $ReleaseLogDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $AppDataDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $ReleaseLogDir | Out-Null
New-Item -ItemType Directory -Force -Path $AppDataDir | Out-Null

$sizeMb = [Math]::Round((Get-Item $InstallerPath).Length / 1MB, 1)
Write-Host "Installer: $InstallerPath"
Write-Host "Installer size: $sizeMb MB"
Write-Host "Install dir: $InstallDir"

Write-Step "Installing silently"
Invoke-CheckedProcess $InstallerPath @("/CURRENTUSER", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/DIR=$InstallDir", "/LOG=$InstallLog") "Installer"

$InstalledExe = Join-Path $InstallDir "TeamsCaptionTranslator.exe"
$Uninstaller = Join-Path $InstallDir "unins000.exe"
Assert-Exists $InstalledExe "Installed application exe missing"
Assert-Exists $Uninstaller "Uninstaller missing"

Write-Step "Running installed smoke test"
$oldSmoke = $env:TCT_SMOKE
$oldOcrSmoke = $env:TCT_PREPARE_OCR_SMOKE
$oldFirstRunSmoke = $env:TCT_FIRST_RUN_SMOKE
$oldAppData = $env:APPDATA
try {
    $env:TCT_SMOKE = "1"
    $env:TCT_PREPARE_OCR_SMOKE = $null
    $env:TCT_FIRST_RUN_SMOKE = $null
    $env:APPDATA = $AppDataDir
    $smoke = Start-Process -FilePath $InstalledExe -Wait -PassThru -WindowStyle Hidden
    if ($smoke.ExitCode -ne 0) {
        throw "Installed application smoke test failed with code $($smoke.ExitCode)"
    }

    Write-Step "Running installed first-run UI smoke test"
    $env:TCT_SMOKE = $null
    $env:TCT_PREPARE_OCR_SMOKE = $null
    $env:TCT_FIRST_RUN_SMOKE = "1"
    $firstRunSmoke = Start-Process -FilePath $InstalledExe -Wait -PassThru -WindowStyle Hidden
    if ($firstRunSmoke.ExitCode -ne 0) {
        throw "Installed first-run UI smoke test failed with code $($firstRunSmoke.ExitCode)"
    }

    if ($OcrSmoke) {
        Write-Step "Running installed OCR preparation smoke test"
        $env:TCT_SMOKE = $null
        $env:TCT_PREPARE_OCR_SMOKE = "1"
        $env:TCT_FIRST_RUN_SMOKE = $null
        $ocrSmokeProcess = Start-Process -FilePath $InstalledExe -Wait -PassThru -WindowStyle Hidden
        if ($ocrSmokeProcess.ExitCode -ne 0) {
            throw "Installed OCR preparation smoke test failed with code $($ocrSmokeProcess.ExitCode)"
        }
    }
}
finally {
    $env:TCT_SMOKE = $oldSmoke
    $env:TCT_PREPARE_OCR_SMOKE = $oldOcrSmoke
    $env:TCT_FIRST_RUN_SMOKE = $oldFirstRunSmoke
    $env:APPDATA = $oldAppData
}

Write-Step "Uninstalling silently"
if (-not $KeepInstall) {
    Invoke-CheckedProcess $Uninstaller @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/LOG=$UninstallLog") "Uninstaller"
    if (Test-Path $InstallDir) {
        throw "Install directory still exists after uninstall: $InstallDir"
    }
}
else {
    Write-Host "KeepInstall enabled; installed files left in place."
}

Write-Step "Release verification passed"
Write-Host "Install log: $InstallLog"
if (-not $KeepInstall) {
    Write-Host "Uninstall log: $UninstallLog"
}
