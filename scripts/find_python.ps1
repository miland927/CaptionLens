$ErrorActionPreference = "SilentlyContinue"

function Test-Python310 {
    param([string]$Path)
    if (-not $Path) {
        return $false
    }
    if ($Path -match "\\AstrBot\\") {
        return $false
    }
    if ($Path -ne "python" -and $Path -ne "py" -and -not (Test-Path -LiteralPath $Path)) {
        return $false
    }
    try {
        $code = "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
        & $Path -c $code | Out-Null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

$candidates = @()

foreach ($root in @($env:LOCALAPPDATA, $env:ProgramFiles, ${env:ProgramFiles(x86)})) {
    if (-not $root) {
        continue
    }
    $candidates += Join-Path $root "Programs\Python\Python312\python.exe"
    $candidates += Join-Path $root "Programs\Python\Python311\python.exe"
    $candidates += Join-Path $root "Programs\Python\Python310\python.exe"
    $candidates += Join-Path $root "Python312\python.exe"
    $candidates += Join-Path $root "Python311\python.exe"
    $candidates += Join-Path $root "Python310\python.exe"
}

$usersRoot = Join-Path $env:SystemDrive "Users"
if (Test-Path -LiteralPath $usersRoot) {
    $candidates += Get-ChildItem -LiteralPath $usersRoot -Directory |
        ForEach-Object {
            Get-ChildItem -LiteralPath (Join-Path $_.FullName "AppData\Local\Programs\Python") -Directory |
                Where-Object { $_.Name -like "Python3*" } |
                ForEach-Object { Join-Path $_.FullName "python.exe" }
        }
}

$command = Get-Command py -ErrorAction SilentlyContinue
if ($command) {
    $candidates += "py"
}
$command = Get-Command python -ErrorAction SilentlyContinue
if ($command) {
    $candidates += $command.Source
}

foreach ($candidate in $candidates | Where-Object { $_ } | Select-Object -Unique) {
    if (Test-Python310 $candidate) {
        Write-Output $candidate
        exit 0
    }
}

exit 1
