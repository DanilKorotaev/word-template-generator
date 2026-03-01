# DEV Guide (RU)

Техническая инструкция по поддержке `word-template-generator`.

## Архитектура

- `src/aosr_generator/generator.py` — загрузка workspace и генерация DOCX.
- `src/aosr_generator/cli.py` — CLI-команды (`ws-build-*`, `ws-validate`, `web-ui`, `ui`).
- `src/aosr_generator/web_ui.py` — FastAPI + встроенный HTML/JS интерфейс.
- `src/aosr_generator/ui.py` — Tkinter UI.

## Локальная разработка

```bash
cd "/Users/danilkorotaev/Nextcloud/ПТО/word-template-generator"
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Базовые команды

```bash
# Web UI (рекомендуется)
aosr-gen web-ui

# Web UI на конкретном порту
aosr-gen web-ui --host 127.0.0.1 --port 8080 --no-open

# Сгенерировать все акты
aosr-gen ws-build-all --workspace-dir "/abs/path/to/workspace"

# Сгенерировать один акт
aosr-gen ws-build-one act-001 --workspace-dir "/abs/path/to/workspace"

# Валидация
aosr-gen ws-validate --workspace-dir "/abs/path/to/workspace"
```

## Диагностика

- Проверить формат markdown: фронтматтер должен начинаться с `---`.
- Проверить шаблон: `template.docx` должен быть доступен в workspace.
- Для missing-полей сверять переменные в DOCX и `fields`/`поля`.

## Local-first ограничения

Текущая версия ожидает локальный путь `workspace` и работает корректно только при локальном запуске Python backend.
Для удалённого хостинга на поддомене требуется отдельная архитектура (см. `docs/DEPLOYMENT_SERVER_RU.md`).
