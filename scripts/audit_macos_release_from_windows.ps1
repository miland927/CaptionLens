param(
    [string]$Version = "0.2.0",
    [string]$ZipPath = ""
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
if (-not $ZipPath) {
    $ZipPath = Join-Path $Root "release\TeamsCaptionTranslator-v$Version-macos.zip"
}

$ReportDir = Join-Path $Root "release"
$Report = Join-Path $ReportDir "MACOS_RELEASE_AUDIT_FROM_WINDOWS_v$Version.txt"
$PackagePrefix = "TeamsCaptionTranslator-v$Version-macos"

$checks = New-Object System.Collections.Generic.List[object]

function Add-Check([string]$Name, [bool]$Pass, [string]$Detail) {
    $script:checks.Add([PSCustomObject]@{
        Name = $Name
        Pass = $Pass
        Detail = $Detail
    })
}

function Read-ZipText($Zip, [string]$EntryName) {
    $entry = $Zip.Entries | Where-Object { $_.FullName -eq $EntryName } | Select-Object -First 1
    if (-not $entry) {
        return $null
    }

    $stream = $entry.Open()
    try {
        $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
        try {
            return $reader.ReadToEnd()
        }
        finally {
            $reader.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

function Get-ZipEntrySha256($Zip, [string]$EntryName) {
    $entry = $Zip.Entries | Where-Object { $_.FullName -eq $EntryName } | Select-Object -First 1
    if (-not $entry) {
        return $null
    }

    $sha = [System.Security.Cryptography.SHA256]::Create()
    $stream = $entry.Open()
    try {
        $hash = $sha.ComputeHash($stream)
        return (($hash | ForEach-Object { $_.ToString("x2") }) -join "").ToUpperInvariant()
    }
    finally {
        $stream.Dispose()
        $sha.Dispose()
    }
}

function Test-NoMojibake([string]$Name, [string]$Text) {
    if ($null -eq $Text) {
        Add-Check "$Name has readable text" $false "missing text"
        return
    }

    $patterns = @(
        [string][char]0x701B,
        [string][char]0x9359,
        [string][char]0x9410,
        [string][char]0x7F01,
        [string][char]0xFFFD
    )
    $bad = @($patterns | Where-Object { $Text.Contains($_) })
    Add-Check "$Name has no common mojibake markers" ($bad.Count -eq 0) ($(if ($bad.Count) { "found: $($bad -join ', ')" } else { "clean" }))
}

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Add-Check "macOS release zip exists" (Test-Path $ZipPath) $ZipPath

if (Test-Path $ZipPath) {
    try {
        Add-Type -AssemblyName System.IO.Compression
        Add-Type -AssemblyName System.IO.Compression.FileSystem

        $zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
        try {
            $entries = @($zip.Entries | ForEach-Object { $_.FullName })
            $requiredEntries = @(
                "$PackagePrefix/TeamsCaptionTranslator-v$Version-macos.dmg",
                "$PackagePrefix/README_MACOS.txt",
                "$PackagePrefix/SEND_TO_MAC_TESTER.txt",
                "$PackagePrefix/MACOS_PACKAGING.md",
                "$PackagePrefix/MAC_TEST_RESULT_TEMPLATE.txt",
                "$PackagePrefix/EXPORT_MACOS_SUPPORT_BUNDLE.sh",
                "$PackagePrefix/RELEASE_MANIFEST.json",
                "$PackagePrefix/SHA256.txt"
            )

            foreach ($required in $requiredEntries) {
                Add-Check "macOS release zip contains $required" (($entries | Where-Object { $_ -eq $required }).Count -eq 1) $required
            }

            $manifestText = Read-ZipText $zip "$PackagePrefix/RELEASE_MANIFEST.json"
            $shaText = Read-ZipText $zip "$PackagePrefix/SHA256.txt"
            $readmeText = Read-ZipText $zip "$PackagePrefix/README_MACOS.txt"
            $testerText = Read-ZipText $zip "$PackagePrefix/SEND_TO_MAC_TESTER.txt"
            $packagingText = Read-ZipText $zip "$PackagePrefix/MACOS_PACKAGING.md"
            $resultTemplateText = Read-ZipText $zip "$PackagePrefix/MAC_TEST_RESULT_TEMPLATE.txt"
            $supportText = Read-ZipText $zip "$PackagePrefix/EXPORT_MACOS_SUPPORT_BUNDLE.sh"

            Test-NoMojibake "README_MACOS.txt" $readmeText
            Test-NoMojibake "SEND_TO_MAC_TESTER.txt" $testerText
            Test-NoMojibake "MACOS_PACKAGING.md" $packagingText
            Test-NoMojibake "MAC_TEST_RESULT_TEMPLATE.txt" $resultTemplateText

            if ($manifestText) {
                try {
                    $manifest = $manifestText | ConvertFrom-Json
                    Add-Check "Manifest platform is macOS" ($manifest.package_platform -eq "macos") "$($manifest.package_platform)"
                    Add-Check "Manifest recommends macOS zip" ($manifest.recommended_zip -eq "TeamsCaptionTranslator-v$Version-macos.zip") "$($manifest.recommended_zip)"
                    Add-Check "Manifest says ordinary users need no Python" ($manifest.ordinary_user_python_required -eq $false) "$($manifest.ordinary_user_python_required)"
                    Add-Check "Manifest records support exporter" ($manifest.support_bundle -eq "EXPORT_MACOS_SUPPORT_BUNDLE.sh") "$($manifest.support_bundle)"
                    Add-Check "Manifest records dmg file" ($manifest.dmg.file -eq "TeamsCaptionTranslator-v$Version-macos.dmg") "$($manifest.dmg.file)"

                    $dmgEntry = "$PackagePrefix/$($manifest.dmg.file)"
                    $dmgHash = Get-ZipEntrySha256 $zip $dmgEntry
                    Add-Check "DMG hash can be computed from zip" ($null -ne $dmgHash) "$dmgEntry"
                    if ($dmgHash) {
                        Add-Check "Manifest dmg SHA256 matches zip entry" ($manifest.dmg.sha256 -eq $dmgHash) "manifest=$($manifest.dmg.sha256); zip=$dmgHash"
                        if ($shaText) {
                            Add-Check "SHA256.txt contains dmg hash" ($shaText -match [Regex]::Escape($dmgHash)) $dmgHash
                        }
                    }

                    $dmgZipEntry = $zip.Entries | Where-Object { $_.FullName -eq $dmgEntry } | Select-Object -First 1
                    if ($dmgZipEntry) {
                        Add-Check "Manifest dmg size matches zip entry" ([int64]$manifest.dmg.size_bytes -eq [int64]$dmgZipEntry.Length) "manifest=$($manifest.dmg.size_bytes); zip=$($dmgZipEntry.Length)"
                    }
                }
                catch {
                    Add-Check "Manifest can be parsed" $false $_.Exception.Message
                }
            }
            else {
                Add-Check "Manifest can be parsed" $false "missing RELEASE_MANIFEST.json"
            }

            if ($testerText) {
                Add-Check "Tester instructions mention Screen Recording" ($testerText -match "Screen Recording") "Screen Recording"
                Add-Check "Tester instructions mention DeepSeek" ($testerText -match "DeepSeek") "DeepSeek"
                Add-Check "Tester instructions warn not to send key" ($testerText -match "Do not send your DeepSeek Key") "Do not send your DeepSeek Key"
                Add-Check "Tester instructions mention support bundle" ($testerText -match "EXPORT_MACOS_SUPPORT_BUNDLE.sh") "EXPORT_MACOS_SUPPORT_BUNDLE.sh"
                Add-Check "Tester instructions mention result template" ($testerText -match "MAC_TEST_RESULT_TEMPLATE.txt") "MAC_TEST_RESULT_TEMPLATE.txt"
            }

            if ($supportText) {
                Add-Check "Support exporter redacts secrets" (($supportText -match "REDACTED") -and ($supportText -match "api\|key\|token\|secret\|password")) "REDACTED api/key/token/secret/password"
                Add-Check "Support exporter avoids Python dependency" (-not ($supportText -match "python3")) "no python3"
            }

            if ($resultTemplateText) {
                Add-Check "Result template records no-Python launch" ($resultTemplateText -match "without installing Python") "without installing Python"
                Add-Check "Result template records real Teams test" ($resultTemplateText -match "real Teams meeting") "real Teams meeting"
                Add-Check "Result template records support bundle check" ($resultTemplateText -match "Support Bundle") "Support Bundle"
            }
        }
        finally {
            $zip.Dispose()
        }
    }
    catch {
        Add-Check "macOS release zip can be inspected" $false $_.Exception.Message
    }
}

$allPass = -not ($checks | Where-Object { -not $_.Pass })
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("Teams Caption Translator v$Version macOS Release Audit From Windows")
$lines.Add("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$lines.Add("Zip: $ZipPath")
$lines.Add("Overall: $(if ($allPass) { 'PASS' } else { 'FAIL' })")
$lines.Add("")
$lines.Add("This audit checks the returned macOS release zip structure, manifest, dmg hash, docs, and support scripts.")
$lines.Add("It does not prove macOS Screen Recording, OCR, or real Teams behavior; those still require a real Mac.")
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
