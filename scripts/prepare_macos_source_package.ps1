param(
    [string]$Version = "0.2.0"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$OutputRoot = Join-Path $Root "release"
$PackageName = "TeamsCaptionTranslator-v$Version-macos-source"
$StagingDir = Join-Path $OutputRoot $PackageName
$ZipPath = Join-Path $OutputRoot "$PackageName.zip"
$ManifestOutputPath = Join-Path $OutputRoot "$PackageName.SOURCE_PACKAGE_MANIFEST.json"

$excludeDirs = @(
    ".git",
    ".claude",
    ".venv",
    ".venv-macos",
    ".pytest_cache",
    "build",
    "build-macos",
    "dist",
    "dist-macos",
    "installer",
    "logs",
    "release",
    "__pycache__"
)

$excludeFiles = @(
    "config.json",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.log",
    ".DS_Store",
    "Thumbs.db"
)

function Test-ExcludedPath([string]$RelativePath) {
    $parts = $RelativePath -split '[\\/]'
    foreach ($part in $parts) {
        if ($excludeDirs -contains $part) {
            return $true
        }
    }
    foreach ($pattern in $excludeFiles) {
        if ([System.Management.Automation.WildcardPattern]::new($pattern).IsMatch((Split-Path $RelativePath -Leaf))) {
            return $true
        }
    }
    return $false
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
Remove-Item -LiteralPath $StagingDir -Recurse -Force -ErrorAction SilentlyContinue
if (Test-Path $ZipPath) {
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    try {
        Remove-Item -LiteralPath $ZipPath -Force
    }
    catch {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $fallbackPackageName = "$PackageName-$timestamp"
        $ZipPath = Join-Path $OutputRoot "$fallbackPackageName.zip"
        $ManifestOutputPath = Join-Path $OutputRoot "$fallbackPackageName.SOURCE_PACKAGE_MANIFEST.json"
        Write-Warning "Default source zip is locked; writing fallback zip: $ZipPath"
    }
}
New-Item -ItemType Directory -Force -Path $StagingDir | Out-Null

function Copy-SourceTree([string]$SourceDir) {
    $rootText = $Root.ToString().TrimEnd('\')
    Get-ChildItem -LiteralPath $SourceDir -Force | ForEach-Object {
        $relative = $_.FullName.Substring($rootText.Length).TrimStart('\')
        if (Test-ExcludedPath $relative) {
            return
        }
        if ($_.PSIsContainer) {
            Copy-SourceTree $_.FullName
            return
        }
        $destination = Join-Path $StagingDir $relative
        New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
    }
}

Copy-SourceTree $Root

$instructions = @"
Teams Caption Translator v$Version macOS source package

Run this on a real Mac:

cd "$PackageName"
bash scripts/build_macos.sh
bash scripts/check_macos_release.sh
bash scripts/prepare_macos_release.sh

Expected final output on the Mac:

release/TeamsCaptionTranslator-v$Version-macos.zip

Notes:

- Python 3.10+ is required on the build Mac.
- The final app should not require ordinary users to install Python.
- The build script prepares and verifies the EasyOCR Japanese models.
- macOS Screen Recording permission must be tested manually.
"@

Set-Content -Path (Join-Path $StagingDir "BUILD_ON_MAC.txt") -Value $instructions -Encoding UTF8

$manifest = [ordered]@{
    name = "Teams Caption Translator macOS source package"
    version = $Version
    package_platform = "macos-source"
    output_zip = [System.IO.Path]::GetFileName($ZipPath)
    ordinary_user_python_required = $false
    build_mac_python_required = "3.10+"
    excludes = [ordered]@{
        directories = $excludeDirs
        files = $excludeFiles
    }
    mac_build_commands = @(
        "bash scripts/build_macos.sh",
        "bash scripts/check_macos_release.sh",
        "bash scripts/prepare_macos_release.sh"
    )
    expected_mac_output = "release/TeamsCaptionTranslator-v$Version-macos.zip"
    notes = @(
        "This source package excludes local config.json and local build artifacts.",
        "The final macOS app should not require ordinary users to install Python.",
        "The build Mac still needs Python 3.10+ to create the packaged app."
    )
}

$manifestPath = Join-Path $StagingDir "SOURCE_PACKAGE_MANIFEST.json"
$manifest | ConvertTo-Json -Depth 10 | Set-Content -Path $manifestPath -Encoding UTF8

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($ZipPath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    Get-ChildItem -LiteralPath $StagingDir -Recurse -File | ForEach-Object {
        $stagingText = (Split-Path $StagingDir -Parent).TrimEnd('\')
        $entryName = $_.FullName.Substring($stagingText.Length).TrimStart('\') -replace '\\', '/'
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $entryName) | Out-Null
    }
}
finally {
    $zip.Dispose()
}

$hash = (Get-FileHash $ZipPath -Algorithm SHA256).Hash
$size = (Get-Item $ZipPath).Length

$manifest.sha256 = $hash
$manifest.size_bytes = $size
$manifest | ConvertTo-Json -Depth 10 | Set-Content -Path $ManifestOutputPath -Encoding UTF8

Write-Host "macOS source package prepared:"
Write-Host $ZipPath
Write-Host "SHA256:"
Write-Host $hash
Write-Host "Size:"
Write-Host "$size bytes"
