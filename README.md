# AOSR Template Generator

Локальный генератор DOCX-актов из markdown для AOСР.

Проект состоит из двух частей:
- **движок** (этот репозиторий с Python-кодом),
- **workspace с документами** (отдельная папка с `template.docx` и актами `*.md`).

## Основной режим работы (local-first)

Приложение рассчитано на запуск **на локальном компьютере пользователя**.
Web UI работает в браузере, но backend остаётся локальным процессом Python и читает/пишет файлы в локальный workspace.

Это важно: если открыть тот же UI на удалённом сервере, текущая модель путей (`/Users/...`, `C:\...`) работать не будет.

## Быстрый старт (macOS)

```bash
cd "/Users/danilkorotaev/Nextcloud/ПТО/word-template-generator"
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
aosr-gen web-ui
```

После запуска откроется браузер с локальным интерфейсом генератора.

## Быстрый старт (Windows PowerShell)

```powershell
cd "C:\path\to\word-template-generator"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
aosr-gen web-ui
```

## One-click запуск для не-IT пользователя

- `start.command` (macOS): запуск в один клик через Finder.
- `start.ps1` (Windows): запуск через PowerShell.

Скрипты сами поднимают `.venv`, ставят зависимости и открывают локальный web-ui.

## Структура workspace

Рекомендуемый вариант:

```text
my-aosr-workspace/
  template.docx
  акт-001-фундамент.md
  act-002-insulation.md
  generated/
  README.md
```

Поддерживаются 2 режима:
- **flat mode**: все `*.md` в корне workspace считаются актами (кроме `README.md` и `project.md`),
- **acts mode**: акты в подпапке `acts/*.md`.

## Инициализация workspace

```bash
aosr-gen init-workspace --workspace-dir "/path/to/my-aosr-workspace"
```

Далее добавьте `template.docx` и файлы актов `*.md`.

## Формат markdown-акта

Используется только YAML front matter:

```md
---
template: template.docx
номер:
  префикс: "КЖ–Б-473–"
  значение: 3
output_name: "3_АОСР_устр_дна_котлована"
поля:
  номер_акта_полный: "[[number]]"
  номер_исп_схемы: "[[number]]"
  название_акта: "..."
---
```

Поддерживаются ключи на русском и английском:
- `fields` / `поля`
- `number` / `номер`
- `prefix` / `префикс`
- `value` / `значение`
- `template` / `шаблон`
- `output_name` / `имя_файла`

Токены вида `[[number]]` и `[[номер]]` поддерживаются.

## Команды (workspace mode)

Сгенерировать всё:

```bash
aosr-gen ws-build-all --workspace-dir "/path/to/my-aosr-workspace"
```

Сгенерировать один акт:

```bash
aosr-gen ws-build-one act-001-foundation --workspace-dir "/path/to/my-aosr-workspace"
```

Проверка валидности:

```bash
aosr-gen ws-validate --workspace-dir "/path/to/my-aosr-workspace"
```

## UI режимы

### Web UI (рекомендуется)

```bash
aosr-gen web-ui
```

Опции:

```bash
aosr-gen web-ui --host 127.0.0.1 --port 8080
aosr-gen web-ui --no-open
```

В интерфейсе:
- указать путь к workspace,
- нажать **Загрузить акты**,
- использовать **Проверить**, **Сгенерировать все**, **Сгенерировать выбранный**.

### Desktop UI (Tkinter)

```bash
aosr-gen ui
```

Если `tkinter` отсутствует, используйте Web UI.

## Частые ошибки

- **Template not found**: в workspace нет файла `template.docx` или указан неверный `template`.
- **No act markdown files found**: в workspace нет актов `*.md` или они в неверной папке.
- **missing values for ...**: в шаблоне DOCX есть переменные, которых нет в `поля`/`fields`.

## Дополнительная документация

- `docs/USER_GUIDE_RU.md` — инструкция для конечного пользователя.
- `docs/OPERATOR_CHECKLIST_RU.md` — короткий чеклист запуска и работы.
- `docs/DEV_GUIDE_RU.md` — технические детали для поддержки.
- `docs/RELEASE_CHECKLIST_RU.md` — чеклист релиза и тестирования.
- `docs/DEPLOYMENT_SERVER_RU.md` — опциональный сценарий серверного деплоя (future-track).

