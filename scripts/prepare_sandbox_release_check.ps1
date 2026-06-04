param(
    [string]$InstallerPath = "",
    [switch]$Launch
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$DefaultInstaller = Join-Path $Root "installer\TeamsCaptionTranslatorSetup-0.2.0.exe"
$SandboxDir = Join-Path $Root "build\sandbox_release_check"
$ResultsDir = Join-Path $SandboxDir "results"
$SandboxScript = Join-Path $SandboxDir "run_inside_sandbox.ps1"
$SandboxConfig = Join-Path $SandboxDir "TeamsCaptionTranslatorReleaseCheck.wsb"

if (-not $InstallerPath) {
    $InstallerPath = $DefaultInstaller
}

$InstallerPath = [System.IO.Path]::GetFullPath($InstallerPath)
if (-not (Test-Path $InstallerPath)) {
    throw "Installer not found: $InstallerPath"
}

Remove-Item -LiteralPath $SandboxDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $SandboxDir | Out-Null
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

$InstallerName = Split-Path $InstallerPath -Leaf
$SandboxInstaller = Join-Path $SandboxDir $InstallerName
Copy-Item -LiteralPath $InstallerPath -Destination $SandboxInstaller -Force

$insideScript = @'
$ErrorActionPreference = "Stop"

$Shared = "C:\Users\WDAGUtilityAccount\Desktop\TCTReleaseCheck"
$Installer = Get-ChildItem -Path $Shared -Filter "TeamsCaptionTranslatorSetup-*.exe" | Select-Object -First 1
$Results = Join-Path $Shared "results"
$InstallDir = "C:\Users\WDAGUtilityAccount\AppData\Local\Programs\Teams Caption Translator Release Check"
$AppDataDir = "C:\Users\WDAGUtilityAccount\AppData\Roaming\TeamsCaptionTranslatorSandboxCheck"
$Log = Join-Path $Results "sandbox-check.log"

function Write-Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Host $line
}

function Quote-ProcessArgument([string]$Argument) {
    if ($Argument -match '[\s"]') {
        return '"' + ($Argument -replace '"', '\"') + '"'
    }
    return $Argument
}

function Invoke-CheckedProcess([string]$FilePath, [string[]]$Arguments, [string]$Label) {
    $argumentLine = ($Arguments | ForEach-Object { Quote-ProcessArgument $_ }) -join " "
    Write-Log "$Label: $FilePath $argumentLine"
    $process = Start-Process -FilePath $FilePath -ArgumentList $argumentLine -Wait -PassThru -WindowStyle Hidden
    Write-Log "$Label exit code: $($process.ExitCode)"
    if ($process.ExitCode -ne 0) {
        throw "$Label failed with code $($process.ExitCode)"
    }
}

try {
    New-Item -ItemType Directory -Force -Path $Results | Out-Null
    Remove-Item -LiteralPath $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $AppDataDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $AppDataDir | Out-Null

    if (-not $Installer) {
        throw "Installer not found in shared folder: $Shared"
    }

    Write-Log "Sandbox release check started."
    Write-Log "Installer: $($Installer.FullName)"
    Write-Log "Installer size: $([Math]::Round($Installer.Length / 1MB, 1)) MB"

    Invoke-CheckedProcess $Installer.FullName @("/CURRENTUSER", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/DIR=$InstallDir", "/LOG=$(Join-Path $Results 'install.log')") "Install"

    $Exe = Join-Path $InstallDir "TeamsCaptionTranslator.exe"
    $Uninstaller = Join-Path $InstallDir "unins000.exe"
    if (-not (Test-Path $Exe)) { throw "Installed exe missing: $Exe" }
    if (-not (Test-Path $Uninstaller)) { throw "Uninstaller missing: $Uninstaller" }

    $oldSmoke = $env:TCT_SMOKE
    $oldOcrSmoke = $env:TCT_PREPARE_OCR_SMOKE
    $oldAppData = $env:APPDATA
    try {
        $env:APPDATA = $AppDataDir
        $env:TCT_SMOKE = "1"
        $env:TCT_PREPARE_OCR_SMOKE = $null
        Invoke-CheckedProcess $Exe @() "App smoke"

        $env:TCT_SMOKE = $null
        $env:TCT_PREPARE_OCR_SMOKE = "1"
        Invoke-CheckedProcess $Exe @() "OCR smoke"
    }
    finally {
        $env:TCT_SMOKE = $oldSmoke
        $env:TCT_PREPARE_OCR_SMOKE = $oldOcrSmoke
        $env:APPDATA = $oldAppData
    }

    $AppLog = Join-Path $AppDataDir "TeamsCaptionTranslator\logs\app.log"
    if (Test-Path $AppLog) {
        Copy-Item -LiteralPath $AppLog -Destination (Join-Path $Results "app.log") -Force
        Write-Log "Copied app log."
    }

    Invoke-CheckedProcess $Uninstaller @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/LOG=$(Join-Path $Results 'uninstall.log')") "Uninstall"
    if (Test-Path $InstallDir) { throw "Install directory still exists after uninstall: $InstallDir" }

    "PASS" | Set-Content -Path (Join-Path $Results "RESULT.txt") -Encoding UTF8
    Write-Log "Sandbox release check PASSED."
}
catch {
    "FAIL: $($_.Exception.Message)" | Set-Content -Path (Join-Path $Results "RESULT.txt") -Encoding UTF8
    Write-Log "Sandbox release check FAILED: $($_.Exception.Message)"
    throw
}
finally {
    Start-Sleep -Seconds 3
}
'@

Set-Content -Path $SandboxScript -Value $insideScript -Encoding UTF8

$escapedSandboxDir = [System.Security.SecurityElement]::Escape($SandboxDir)
$wsb = @"
<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>$escapedSandboxDir</HostFolder>
      <SandboxFolder>C:\Users\WDAGUtilityAccount\Desktop\TCTReleaseCheck</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\WDAGUtilityAccount\Desktop\TCTReleaseCheck\run_inside_sandbox.ps1</Command>
  </LogonCommand>
</Configuration>
"@

Set-Content -Path $SandboxConfig -Value $wsb -Encoding UTF8

Write-Host "Sandbox release-check package prepared:"
Write-Host "  $SandboxDir"
Write-Host "Sandbox config:"
Write-Host "  $SandboxConfig"
Write-Host ""
Write-Host "If Windows Sandbox is available, open the .wsb file and wait for results in:"
Write-Host "  $ResultsDir"

if ($Launch) {
    $sandbox = Get-Command WindowsSandbox.exe -ErrorAction SilentlyContinue
    if (-not $sandbox) {
        throw "WindowsSandbox.exe was not found. Enable Windows Sandbox or run this on Windows Pro/Enterprise with Sandbox support."
    }
    Start-Process -FilePath $SandboxConfig
}
