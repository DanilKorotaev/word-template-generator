$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERR] Python не найден. Установите Python 3.10+."
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "[RUN] Создание виртуального окружения..."
    python -m venv .venv
}

& ".venv\Scripts\Activate.ps1"

Write-Host "[RUN] Установка/обновление зависимостей..."
python -m pip install --upgrade pip | Out-Null
python -m pip install -e .

Write-Host "[RUN] Запуск Word Template Generator Web UI..."
word-gen web-ui
