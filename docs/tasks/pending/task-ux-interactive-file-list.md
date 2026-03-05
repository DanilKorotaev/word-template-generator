# Задача: Интерактивный список сгенерированных файлов

**Статус**: 📋 Запланировано  
**Приоритет**: 🔴 Высокий  
**Категория**: Улучшения UX

## Описание

После генерации документов результаты отображаются только в текстовом логе (`[OK] act.md -> /path/to/file.docx`). Пользователь не может открыть сгенерированный файл прямо из интерфейса — приходится вручную искать его в проводнике.

Нужно добавить интерактивную секцию с карточками/списком сгенерированных файлов, где каждый файл можно открыть в Word одним кликом (кнопка или двойной клик).

## Проблема

Текущий UX после генерации:
1. Лог показывает `[OK] act.md -> C:\Users\...\generated\output.docx`
2. Пользователь копирует путь или открывает проводник
3. Находит файл вручную и открывает

Это неудобно, особенно при генерации множества файлов.

## Решение

### UI: Секция «Результаты»

Добавить новый блок `card` между секцией «Генерация» и «Логи»:

```html
<div class="card" id="resultsCard" style="display: none;">
  <div class="section-title">Результаты</div>
  <div id="resultsList" class="results-list"></div>
</div>
```

Каждый файл отображается как элемент списка:

```html
<div class="result-item">
  <span class="result-icon">📄</span>
  <span class="result-name">Акт-01.docx</span>
  <span class="result-path">/path/to/generated/Акт-01.docx</span>
  <button class="secondary result-open" onclick="openFile('/path/to/file.docx')">
    Открыть
  </button>
</div>
```

### Backend: Эндпоинт для открытия файла

Новый API endpoint:

```python
@router.post("/api/open-file")
def open_file(payload: OpenFilePayload):
    """Открыть файл в ассоциированном приложении (Word)."""
    file_path = Path(payload.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    import subprocess, sys
    if sys.platform == "win32":
        os.startfile(str(file_path))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(file_path)])
    else:
        subprocess.Popen(["xdg-open", str(file_path)])
    
    return {"status": "ok"}
```

### Данные: расширение ответа API

Эндпоинты `build-all` и `build-one` должны возвращать не только `log`, но и `files`:

```json
{
  "log": ["[OK] act.md -> /path/file.docx"],
  "files": [
    {
      "act": "act.md",
      "path": "/path/to/generated/Акт-01.docx",
      "name": "Акт-01.docx"
    }
  ]
}
```

## Задачи

### 1. Расширить ответ API генерации

- [ ] Обновить `build-all` и `build-one` в `routes.py`: собирать список `files` из `BuildResult`
- [ ] Каждый файл: `{"act": str, "path": str, "name": str}`
- [ ] Путь передавать как абсолютный (для OS-уровневого открытия)

### 2. Создать эндпоинт `/api/open-file`

- [ ] Создать `OpenFilePayload` в `schemas.py` с полем `path: str`
- [ ] Реализовать кроссплатформенное открытие: `os.startfile` (Win), `open` (macOS), `xdg-open` (Linux)
- [ ] Валидация: файл должен существовать, расширение `.docx` или `.docm`
- [ ] Безопасность: ограничить пути только в пределах workspace (опционально)

### 3. Добавить UI секцию «Результаты»

- [ ] Добавить HTML-блок `resultsCard` в `index.html` (скрыт по умолчанию)
- [ ] Стилизовать `.results-list`, `.result-item` в `style.css`
- [ ] Элементы: иконка, имя файла, полный путь (мелким шрифтом), кнопка «Открыть»
- [ ] Двойной клик по строке = открыть файл

### 4. Обновить JS-логику

- [ ] После успешной генерации: распарсить `data.files`, отрисовать список
- [ ] Функция `renderResults(files)` — заполняет `#resultsList`
- [ ] Функция `openFile(path)` — POST `/api/open-file`
- [ ] При новой генерации — очищать и заполнять заново
- [ ] Если `files` пуст — скрыть секцию

### 5. Очистка и состояние

- [ ] Кнопка «Очистить» в секции результатов (или автоочистка при перегенерации)
- [ ] Сохранять видимость секции при смене workspace

## Технические детали

- `os.startfile()` — только Windows; на macOS используем `open`, на Linux — `xdg-open`
- Все три варианта запускают файл в ассоциированном приложении (обычно Microsoft Word для `.docx`)
- Безопасность: endpoint принимает произвольный путь; стоит подумать об ограничении на workspace
- Файл открывается на **сервере**, а не в браузере — это корректно для локального режима

## Связанные файлы

- `src/word_template_generator/web/routes.py` — новый endpoint + обновление build endpoints
- `src/word_template_generator/web/schemas.py` — `OpenFilePayload`
- `src/word_template_generator/web/static/index.html` — секция «Результаты»
- `src/word_template_generator/web/static/app.js` — `renderResults()`, `openFile()`
- `src/word_template_generator/web/static/style.css` — стили `.result-*`

## Связанные задачи

- [Обработка блокировки файла при перегенерации](task-ux-file-lock-handling.md) — закрытие файла перед перезаписью
- [Открытие шаблона из UI](task-ux-open-template.md) — аналогичный механизм для шаблонов

## Оценка

- **Сложность**: 🟡 Средняя
- **Время**: ~3-4 часа
- Основная сложность — кроссплатформенное открытие файлов и безопасность endpoint
