param(
    [string]$InstallerPath = "",
    [string]$Version = "0.2.0"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$Generator = Join-Path $Root "scripts\prepare_release_package.py"

if (Test-Path $VenvPython) {
    & $VenvPython -c "import sys" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $Python = $VenvPython
    }
}

if (-not $Python) {
    $command = Get-Command python -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Python was not found. Run scripts\run.bat once or install Python 3.10+."
    }
    $Python = $command.Source
}

$argsList = @($Generator, "--version", $Version)
if ($InstallerPath) {
    $argsList += @("--installer", $InstallerPath)
}

& $Python @argsList
if ($LASTEXITCODE -ne 0) {
    throw "Release package generation failed with exit code $LASTEXITCODE"
}
