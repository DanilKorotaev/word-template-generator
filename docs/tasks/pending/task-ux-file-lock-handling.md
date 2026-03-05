# Задача: Обработка блокировки файла при перегенерации

**Статус**: 📋 Запланировано  
**Приоритет**: 🔴 Высокий  
**Категория**: Улучшения UX

## Описание

При перегенерации документа, если `.docx` файл уже открыт в Microsoft Word, `tpl.save()` выбрасывает `PermissionError` (Windows блокирует файл). Пользователю приходится вручную закрывать Word, что неудобно и ломает рабочий процесс.

## Проблема

Текущий код в `core/generator.py` просто вызывает `tpl.save(str(output_file))` без проверки блокировки:

```python
tpl.save(str(output_file))
```

На Windows, если файл открыт в Word, это приводит к `PermissionError: [Errno 13] Permission denied`. Ошибка пробрасывается наверх и отображается как `[ERR]` в логах. Пользователь вынужден:
1. Закрыть файл в Word
2. Снова нажать «Сгенерировать»

## Решение

Многоуровневый подход:

### Стратегия 1: Попытка закрыть файл в Word через COM (Windows)

На Windows можно использовать `pywin32` (`win32com.client`) для программного закрытия файла:

```python
import win32com.client

def close_word_document(file_path: Path) -> bool:
    """Попытаться закрыть документ в Word, если он открыт."""
    try:
        word = win32com.client.GetActiveObject("Word.Application")
        for doc in word.Documents:
            if Path(doc.FullName).resolve() == file_path.resolve():
                doc.Close(SaveChanges=False)
                return True
    except Exception:
        pass
    return False
```

### Стратегия 2: Fallback — сохранение в альтернативный файл

Если закрыть не удалось (Word не отвечает, или macOS/Linux):

```python
output_file_alt = output_file.with_stem(f"{output_file.stem}_new")
tpl.save(str(output_file_alt))
```

С уведомлением пользователя, что файл сохранён под другим именем.

### Стратегия 3: Retry с ожиданием

После попытки закрытия — подождать 1-2 секунды и повторить `save()`.

## Задачи

### 1. Определить блокировку файла

- [ ] Создать утилиту `utils/file_lock.py` с функцией `is_file_locked(path: Path) -> bool`
- [ ] На Windows: попытка открыть файл на запись; если `PermissionError` — заблокирован
- [ ] На macOS/Linux: `fcntl.flock` или аналогичная проверка (опционально)

### 2. Закрытие файла в Word (Windows)

- [ ] Создать функцию `close_word_document(file_path: Path) -> bool` в `utils/file_lock.py`
- [ ] Использовать `win32com.client` для доступа к запущенному Word
- [ ] Безопасно обработать отсутствие `pywin32` (try/except ImportError)
- [ ] Закрывать документ без сохранения (это сгенерированный файл)

### 3. Обновить `core/generator.py`

- [ ] Перед `tpl.save()` проверить `is_file_locked(output_file)`
- [ ] Если заблокирован: попробовать `close_word_document()`, подождать, повторить
- [ ] Если повторная попытка не удалась: сохранить в `_new.docx`, добавить warning в `BuildResult`
- [ ] Добавить поле `warnings: list[str]` в `BuildResult` для передачи предупреждений

### 4. Обновить API и фронтенд

- [ ] В `routes.py`: передавать warnings из `BuildResult` в лог
- [ ] В `app.js`: отображать warnings как `[WARN]` в логах и toast

## Технические детали

- `pywin32` — опциональная зависимость (только Windows)
- На macOS/Linux блокировки файлов не так агрессивны, но fallback через альтернативное имя всё равно полезен
- COM-объект Word может быть недоступен, если Word запущен от другого пользователя

## Связанные файлы

- `src/word_template_generator/core/generator.py` — `build_one()`, `tpl.save()`
- `src/word_template_generator/core/models.py` — `BuildResult`
- `src/word_template_generator/utils/file_lock.py` — новый модуль
- `src/word_template_generator/web/routes.py` — передача warnings
- `src/word_template_generator/web/static/app.js` — отображение warnings

## Оценка

- **Сложность**: 🟡 Средняя
- **Время**: ~3-4 часа
- Основная сложность — COM-взаимодействие с Word и кроссплатформенность
