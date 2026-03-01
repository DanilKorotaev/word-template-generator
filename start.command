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

VENV_PY=".venv/bin/python3"
if [ ! -x "$VENV_PY" ]; then
  VENV_PY=".venv/bin/python"
fi

if [ ! -x "$VENV_PY" ]; then
  echo "[ERR] Не найден Python внутри .venv. Пересоздайте окружение."
  read -r -p "Нажмите Enter для выхода..."
  exit 1
fi

echo "[RUN] Установка/обновление зависимостей..."
"$VENV_PY" -m pip install --upgrade pip >/dev/null
"$VENV_PY" -m pip install -e .

echo "[RUN] Запуск Word Template Generator Web UI..."
"$VENV_PY" -m word_template_generator.cli web-ui
