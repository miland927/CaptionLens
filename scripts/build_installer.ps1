param(
    [switch]$SkipInno
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$Spec = Join-Path $Root "packaging\teams-caption-translator.spec"
$InnoScript = Join-Path $Root "packaging\teams-caption-translator.iss"
$OutputDir = Join-Path $Root "installer"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating .venv via scripts\run.bat first..."
    & (Join-Path $Root "scripts\run.bat")
}

if (-not (Test-Path $VenvPython)) {
    throw ".venv was not created. Run scripts\run.bat once and try again."
}

Write-Host "Installing build dependencies..."
& $VenvPython -m pip install --upgrade pyinstaller

Write-Host "Building frozen application..."
Push-Location $Root
& $VenvPython -m PyInstaller --noconfirm --distpath (Join-Path $Root "dist") --workpath (Join-Path $Root "build") $Spec
$pyinstallerExit = $LASTEXITCODE
Pop-Location
if ($pyinstallerExit -ne 0) {
    throw "PyInstaller failed with exit code $pyinstallerExit"
}

if ($SkipInno) {
    Write-Host "SkipInno enabled. Building self-extracting user installer..."
    & $VenvPython (Join-Path $Root "scripts\make_self_extracting_installer.py")
    if ($LASTEXITCODE -ne 0) {
        throw "Self-extracting installer build failed with exit code $LASTEXITCODE"
    }
    exit 0
}

$isccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)
$Iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $Iscc) {
    Write-Host "Inno Setup 6 not found. Building self-extracting user installer instead..."
    & $VenvPython (Join-Path $Root "scripts\make_self_extracting_installer.py")
    if ($LASTEXITCODE -ne 0) {
        throw "Self-extracting installer build failed with exit code $LASTEXITCODE"
    }
    exit 0
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Write-Host "Building Windows installer..."
& $Iscc $InnoScript
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE"
}
Write-Host "Installer output: $OutputDir"
