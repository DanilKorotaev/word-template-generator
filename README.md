# Word Template Generator

Локальный генератор DOCX-актов из markdown для AOСР.

Проект состоит из двух частей:
- **движок** (этот репозиторий с Python-кодом),
- **workspace с документами** (отдельная папка с `template.docx` и актами `*.md`).

## Запуск за 1 минуту (для пользователя)

1. Откройте папку проекта `word-template-generator`.
2. Запустите:
   - на macOS: `start.command`
   - на Windows: `start.ps1`
3. Дождитесь открытия браузера с интерфейсом.
4. В интерфейсе:
   - выберите папку `workspace`,
   - нажмите `Загрузить акты`,
   - нажмите `Сгенерировать все`.

Готовые файлы появятся в папке `generated/` внутри вашего `workspace`.

## Основной режим работы (local-first)

Приложение рассчитано на запуск **на локальном компьютере пользователя**.
Web UI работает в браузере, но backend остаётся локальным процессом Python и читает/пишет файлы в локальный workspace.

Это важно: если открыть тот же UI на удалённом сервере, текущая модель путей (`/Users/...`, `C:\...`) работать не будет.

## Быстрый старт (macOS)

```bash
cd "/path/to/word-template-generator"
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
word-gen web-ui
```

После запуска откроется браузер с локальным интерфейсом генератора.

## Быстрый старт (Windows PowerShell)

```powershell
cd "C:\path\to\word-template-generator"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
word-gen web-ui
```

Полная инструкция для Windows:
- `docs/WINDOWS_SETUP_RU.md`

## One-click запуск для не-IT пользователя

- `start.command` (macOS): запуск в один клик через Finder.
- `start.ps1` (Windows): запуск через PowerShell.

Скрипты сами поднимают `.venv`, ставят зависимости и открывают локальный web-ui.

## Структура workspace

Рекомендуемый вариант:

```text
my-word-workspace/
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
word-gen init-workspace --workspace-dir "/path/to/my-word-workspace"
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
  объект: "дом Б-473"
  описание: "Работы по [[объект]]"
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

`output_name` / `имя_файла` опционален.  
Если он не указан, итоговый `.docx` получает имя markdown-файла акта.

Поддерживаются токены `[[...]]` в строковых полях:
- `[[number]]` / `[[номер]]`,
- а также ссылки на любые другие поля, например `описание: "Работы по [[объект]]"`.

Поддерживается форматирование дат в токенах:
- `[[дата|dd.MM.yyyy]]` -> `04.03.2026`
- `[[дата|d MMMMG yyyy г.]]` -> `4 марта 2026 г.`
- `[[today]]` / `[[сегодня]]` -> текущая дата в формате `dd.MM.yyyy`
- `[[today|d MMMMG yyyy]]` -> текущая дата с нужным форматом

Поддерживаемые входные форматы дат:
- `dd.MM.yyyy` (например, `04.03.2026`)
- `yyyy-MM-dd` (ISO)
- `dd/MM/yyyy`

Если значение поля равно `today` или `сегодня`, оно автоматически преобразуется в текущую дату.
Невалидные даты (например, `32.13.2026`) вызывают `ValueError` с понятным сообщением.

Важно: циклические ссылки токенов (A -> B -> A) вызывают ошибку валидации.

Для спецсимволов в YAML используйте корректное экранирование:
- `\"` для двойных кавычек внутри строки в двойных кавычках;
- `''` для одинарной кавычки внутри строки в одинарных кавычках;
- `\\` для обратного слэша;
- `|` для буквальных переносов строк и `>` для folded-текста.

## Команды (workspace mode)

Сгенерировать всё:

```bash
word-gen ws-build-all --workspace-dir "/path/to/my-word-workspace"
```

Сгенерировать один акт:

```bash
word-gen ws-build-one act-001-foundation --workspace-dir "/path/to/my-word-workspace"
```

Проверка валидности:

```bash
word-gen ws-validate --workspace-dir "/path/to/my-word-workspace"
```

## UI режимы

### Web UI (рекомендуется)

```bash
word-gen web-ui
```

Опции:

```bash
word-gen web-ui --host 127.0.0.1 --port 8090
word-gen web-ui --no-open
```

По умолчанию Web UI запускается на `127.0.0.1:8090`.  
Для сохранения истории в блоке "Недавние проекты" используйте один и тот же адрес/порт.

В интерфейсе:
- указать путь к workspace,
- нажать **Загрузить акты**,
- использовать **Проверить**, **Сгенерировать все**, **Сгенерировать выбранный**.

### Desktop UI (Tkinter)

```bash
word-gen ui
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
- `docs/GIT_FLOW_RU.md` — процесс ветвления и релизов по GitFlow.
- `agent/system_prompt.md` — системный промпт проекта для AI-ассистента.

