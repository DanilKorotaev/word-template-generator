# Установка и запуск на Windows

Инструкция для первого запуска `word-template-generator` на Windows 10/11.

## 1) Что установить

- **Python 3.10+** с официального сайта: `https://www.python.org/downloads/windows/`
- Во время установки обязательно отметить:
  - `Add python.exe to PATH`
  - `Install launcher for all users (recommended)`

Проверка после установки (в новом PowerShell):

```powershell
python --version
py --version
```

Если хотя бы одна команда показывает версию Python — всё в порядке.

## 2) Разрешить запуск скрипта `start.ps1`

Откройте PowerShell **от имени пользователя** и выполните:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Если появится запрос подтверждения, выберите `Y`.

## 3) Запуск проекта

Откройте PowerShell и выполните:

```powershell
cd "C:\path\to\word-template-generator"
.\start.ps1
```

Скрипт автоматически:
- создаст `.venv` (если его нет),
- установит зависимости,
- запустит Web UI.

## 4) Что нужно для работы генератора

- Папка `workspace` с:
  - `template.docx`
  - актами `*.md`
  - папкой `generated/` (может создаться автоматически)

После запуска в UI:
1. укажите путь к `workspace`,
2. нажмите `Загрузить акты`,
3. затем `Проверить` и `Сгенерировать все`.

## 5) Частые ошибки на Windows

### `python: command not found`
- Python не установлен или не добавлен в PATH.
- Переустановите Python с галкой `Add python.exe to PATH`.

### `running scripts is disabled on this system`
- Не задана политика выполнения PowerShell.
- Выполните:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```

### `No module named word_template_generator`
- Пакет не установлен в `.venv`.
- Запустите `.\start.ps1` заново (он сам выполнит `pip install -e .`).

### Web UI не открылся автоматически
- Откройте вручную URL из терминала (обычно `http://127.0.0.1:<port>`).
