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

WEB_UI_HOST="${WEB_UI_HOST:-127.0.0.1}"
WEB_UI_PORT="${WEB_UI_PORT:-8090}"

echo "[RUN] Проверка уже запущенного Web UI на порту $WEB_UI_PORT..."
EXISTING_PIDS="$(lsof -ti tcp:"$WEB_UI_PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [ -n "$EXISTING_PIDS" ]; then
  echo "[RUN] Найден существующий процесс(ы): $EXISTING_PIDS"
  echo "[RUN] Остановка существующего Web UI..."
  kill $EXISTING_PIDS 2>/dev/null || true
  sleep 0.4
  STILL_RUNNING="$(lsof -ti tcp:"$WEB_UI_PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$STILL_RUNNING" ]; then
    echo "[RUN] Принудительная остановка процесса(ов): $STILL_RUNNING"
    kill -9 $STILL_RUNNING 2>/dev/null || true
  fi
fi

echo "[RUN] Запуск Word Template Generator Web UI на $WEB_UI_HOST:$WEB_UI_PORT..."
"$VENV_PY" -m word_template_generator.cli web-ui --host "$WEB_UI_HOST" --port "$WEB_UI_PORT"
