$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "[ERR] Python не найден. Установите Python 3.10+ и перезапустите терминал."
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "[RUN] Создание виртуального окружения..."
    if ($pythonCmd.Name -eq "py") {
        py -3 -m venv .venv
    } else {
        python -m venv .venv
    }
}

$venvPython = ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[ERR] Не найден Python внутри .venv. Пересоздайте окружение."
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "[RUN] Установка/обновление зависимостей..."
& $venvPython -m pip install --upgrade pip | Out-Null
& $venvPython -m pip install -e .

Write-Host "[RUN] Запуск Word Template Generator Web UI..."
& $venvPython -m word_template_generator.cli web-ui
