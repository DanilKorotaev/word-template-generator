#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERR] python3 не найден. Установите Python 3.10+."
  read -r -p "Нажмите Enter для выхода..."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[RUN] Создание виртуального окружения..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "[RUN] Установка/обновление зависимостей..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -e .

echo "[RUN] Запуск AOSR Web UI..."
aosr-gen web-ui
