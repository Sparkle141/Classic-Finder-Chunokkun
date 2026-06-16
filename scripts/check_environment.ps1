param(
    [string]$Python = $env:CLASSIC_FINDER_PYTHON
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

try {
    $utf8 = [System.Text.UTF8Encoding]::new()
    [Console]::OutputEncoding = $utf8
    $OutputEncoding = $utf8
} catch {
    Write-Host "[WARN] Could not switch console output to UTF-8: $($_.Exception.Message)"
}

$Problems = New-Object System.Collections.Generic.List[string]
$PythonCommand = $null

function Add-Ok {
    param([string]$Message)
    Write-Host "[OK] $Message"
}

function Add-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message"
}

function Add-Problem {
    param([string]$Message)
    $Problems.Add($Message) | Out-Null
    Write-Host "[FAIL] $Message"
}

function Test-PythonCommand {
    param([string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        return $false
    }

    $source = [string]$command.Source
    if ($source -match "\\WindowsApps\\") {
        Add-Warn "$Name resolves to a Microsoft Store app execution alias: $source"
        return $false
    }

    try {
        $version = & $Name --version 2>&1
        if ($LASTEXITCODE -eq 0 -and "$version" -match "^Python 3\.") {
            $script:PythonCommand = $Name
            Add-Ok "Python runtime found: $Name ($version)"
            return $true
        }
        Add-Warn "$Name exists but did not report Python 3: $version"
    } catch {
        Add-Warn "$Name exists but could not run: $($_.Exception.Message)"
    }

    return $false
}

function Test-PythonExecutable {
    param([string]$Path)

    if (-not $Path -or -not (Test-Path -LiteralPath $Path)) {
        return $false
    }

    try {
        $version = & $Path --version 2>&1
        if ($LASTEXITCODE -eq 0 -and "$version" -match "^Python 3\.") {
            $script:PythonCommand = $Path
            Add-Ok "Python runtime found: $Path ($version)"
            return $true
        }
        Add-Warn "$Path exists but did not report Python 3: $version"
    } catch {
        Add-Warn "$Path exists but could not run: $($_.Exception.Message)"
    }

    return $false
}

if ($Python) {
    Test-PythonExecutable $Python | Out-Null
}

foreach ($candidate in @("python", "python3", "py")) {
    if ($PythonCommand -or (Test-PythonCommand $candidate)) {
        break
    }
}

if (-not $PythonCommand) {
    $pathCandidates = @()
    if ($env:LOCALAPPDATA) {
        $pathCandidates += Get-ChildItem -ErrorAction SilentlyContinue -Path "$env:LOCALAPPDATA\Programs\Python" -Filter python.exe -Recurse
    }
    if ($env:ProgramFiles) {
        $pathCandidates += Get-ChildItem -ErrorAction SilentlyContinue -Path $env:ProgramFiles -Filter python.exe -Depth 3
    }
    if (${env:ProgramFiles(x86)}) {
        $pathCandidates += Get-ChildItem -ErrorAction SilentlyContinue -Path ${env:ProgramFiles(x86)} -Filter python.exe -Depth 3
    }
    foreach ($candidate in $pathCandidates | Select-Object -ExpandProperty FullName -Unique) {
        if (Test-PythonExecutable $candidate) {
            break
        }
    }
}

if (-not $PythonCommand) {
    Add-Problem "No usable Python 3 runtime found. Install Python 3.10+, add it to PATH, or run this script with -Python `"C:\Path\To\python.exe`". Disable Windows App execution aliases if they point to Microsoft Store."
}

$jsonFailures = 0
Get-ChildItem -Path $ProjectRoot -Recurse -Filter *.json | ForEach-Object {
    try {
        Get-Content -Raw -Encoding UTF8 -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null
    } catch {
        $jsonFailures += 1
        Add-Problem "Invalid JSON: $($_.FullName) - $($_.Exception.Message)"
    }
}

if ($jsonFailures -eq 0) {
    Add-Ok "JSON files parse as UTF-8 JSON."
}

if ($PythonCommand) {
    try {
        & $PythonCommand scripts/smoke_test_reverse_trace.py
        if ($LASTEXITCODE -eq 0) {
            Add-Ok "Reverse-trace smoke test passed."
        } else {
            Add-Problem "Reverse-trace smoke test exited with code $LASTEXITCODE."
        }
    } catch {
        Add-Problem "Reverse-trace smoke test failed: $($_.Exception.Message)"
    }
}

if ($Problems.Count -gt 0) {
    Write-Host ""
    Write-Host "Environment check completed with $($Problems.Count) problem(s)."
    exit 1
}

Write-Host ""
Write-Host "Environment check passed."
