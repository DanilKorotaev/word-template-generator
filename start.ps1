$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

function Test-PythonLauncher {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [string[]]$Args = @("--version")
    )
    try {
        $null = & $Name @Args
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Find-PythonExePath {
    $candidates = @()

    # Typical python.org per-user installs
    if ($env:LocalAppData) {
        $candidates += Get-ChildItem "$env:LocalAppData\Programs\Python\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    }
    # Typical all-users installs
    if ($env:ProgramFiles) {
        $candidates += Get-ChildItem "$env:ProgramFiles\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    }
    if (${env:ProgramFiles(x86)}) {
        $candidates += Get-ChildItem "${env:ProgramFiles(x86)}\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    }

    foreach ($exe in $candidates | Sort-Object -Descending) {
        try {
            $null = & $exe --version
            if ($LASTEXITCODE -eq 0) {
                return $exe
            }
        } catch {
            continue
        }
    }
    return $null
}

$pythonMode = $null
$pythonPath = $null

if (Get-Command py -ErrorAction SilentlyContinue) {
    if (Test-PythonLauncher -Name "py" -Args @("-3", "--version")) {
        $pythonMode = "py"
    }
}

if (-not $pythonMode -and (Get-Command python -ErrorAction SilentlyContinue)) {
    if (Test-PythonLauncher -Name "python" -Args @("--version")) {
        $pythonMode = "python"
    }
}

if (-not $pythonMode) {
    $pythonPath = Find-PythonExePath
    if ($pythonPath) {
        $pythonMode = "path"
    }
}

if (-not $pythonMode) {
    Write-Host "[ERR] Working Python 3 not found."
    Write-Host "[TIP] Install Python 3.10+ from https://www.python.org/downloads/windows/"
    Write-Host "[TIP] Disable Microsoft Store python alias in Settings -> App execution aliases."
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "[RUN] Creating virtual environment..."
    if ($pythonMode -eq "py") {
        py -3 -m venv .venv
    } elseif ($pythonMode -eq "path") {
        & $pythonPath -m venv .venv
    } else {
        python -m venv .venv
    }
}

$venvPythonCandidates = @(
    ".venv\Scripts\python.exe",
    ".venv\Scripts\python"
)
$venvPython = $venvPythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $venvPython) {
    Write-Host "[ERR] Python inside .venv was not found."
    Write-Host "[TIP] Delete .venv folder and run start.bat again."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[RUN] Installing/updating dependencies..."
& $venvPython -m pip install --upgrade pip | Out-Null
& $venvPython -m pip install -e .

Write-Host "[RUN] Starting Word Template Generator Web UI..."
& $venvPython -m word_template_generator.cli web-ui
