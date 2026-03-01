# DEV Guide (RU)

Техническая инструкция по поддержке `word-template-generator`.

## Архитектура

- `src/word_template_generator/cli.py` — CLI-команды и точка входа.
- `src/word_template_generator/generator.py` — ядро загрузки workspace и генерации DOCX.
- `src/word_template_generator/web_ui.py` — FastAPI + встроенный HTML/JS интерфейс.
- `src/word_template_generator/ui.py` — Tkinter UI.

## Локальная разработка

```bash
cd "/path/to/word-template-generator"
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Базовые команды

```bash
# Web UI (рекомендуется)
word-gen web-ui

# Web UI на конкретном порту
word-gen web-ui --host 127.0.0.1 --port 8080 --no-open

# Сгенерировать все акты
word-gen ws-build-all --workspace-dir "/abs/path/to/workspace"

# Сгенерировать один акт
word-gen ws-build-one act-001 --workspace-dir "/abs/path/to/workspace"

# Валидация
word-gen ws-validate --workspace-dir "/abs/path/to/workspace"
```

## Диагностика

- Проверить формат markdown: фронтматтер должен начинаться с `---`.
- Проверить шаблон: `template.docx` должен быть доступен в workspace.
- Для missing-полей сверять переменные в DOCX и `fields`/`поля`.

## Local-first ограничения

Текущая версия ожидает локальный путь `workspace` и работает корректно только при локальном запуске Python backend.
Для удалённого хостинга на поддомене требуется отдельная архитектура (см. `docs/DEPLOYMENT_SERVER_RU.md`).
