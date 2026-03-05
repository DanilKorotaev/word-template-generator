# Задача: Открытие шаблона из интерфейса

**Статус**: 📋 Запланировано  
**Приоритет**: 🟡 Средний  
**Категория**: Улучшения UX

## Описание

Сейчас шаблон `.docx`/`.docm` можно только выбрать из выпадающего списка для генерации. Нет возможности быстро открыть шаблон в Word для просмотра или редактирования плейсхолдеров — приходится искать файл в проводнике вручную.

Нужно добавить кнопку «Открыть шаблон» рядом с выпадающим списком шаблонов, чтобы одним кликом открыть выбранный шаблон в Word.

## Проблема

Рабочий процесс инженера ПТО:
1. Сгенерировать документ → посмотреть → увидеть, что плейсхолдер не тот
2. Нужно открыть шаблон, поправить → снова сгенерировать
3. Сейчас: вручную искать файл в проводнике, открывать

## Решение

### UI

Добавить кнопку «Открыть» рядом с `<select id="templateSelect">`:

```html
<div class="row row-wrap">
  <label for="templateSelect">Шаблон</label>
  <select id="templateSelect" class="grow"></select>
  <button class="secondary" onclick="openTemplate()">Открыть шаблон</button>
</div>
```

### Backend

Переиспользовать endpoint `/api/open-file` из задачи [Интерактивный список файлов](task-ux-interactive-file-list.md). Для определения полного пути к шаблону:

Вариант А: Фронтенд знает путь workspace + templates_dir + имя файла — может собрать путь сам.

Вариант Б: Добавить эндпоинт `/api/template-path`, который возвращает абсолютный путь к шаблону:

```python
@router.get("/api/template-path")
def template_path(workspace: str, template: str) -> dict[str, str]:
    cfg, _ = load_workspace(Path(workspace))
    path = cfg.templates_dir / template
    if not path.exists():
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return {"path": str(path)}
```

### JS

```javascript
async function openTemplate() {
  const template = selectedTemplate();
  if (!template) {
    showToast("Сначала выберите шаблон", "error");
    return;
  }
  const workspace = ws();
  // Получить полный путь к шаблону и открыть
  const res = await fetch(`/api/template-path?workspace=${encodeURIComponent(workspace)}&template=${encodeURIComponent(template)}`);
  const data = await res.json();
  if (!res.ok) { ... }
  await openFile(data.path);
}
```

## Задачи

### 1. Добавить кнопку в UI

- [ ] Добавить кнопку «Открыть шаблон» рядом с select шаблонов в `index.html`
- [ ] Кнопка неактивна, если шаблон не выбран (disabled)
- [ ] При смене select — обновлять состояние кнопки

### 2. Реализовать получение пути к шаблону

- [ ] Вариант А: передавать `templates_dir` с бэкенда в ответе `/api/acts`
- [ ] Вариант Б: создать endpoint `/api/template-path` (проще и надёжнее)
- [ ] Валидация: шаблон должен существовать

### 3. Реализовать `openTemplate()` в JS

- [ ] Получить полный путь к шаблону через API
- [ ] Вызвать `openFile(path)` (переиспользовать из задачи интерактивного списка)
- [ ] Обработка ошибок: шаблон не выбран, файл не найден

### 4. Аналогично для output-директории

- [ ] Кнопка «Открыть папку» рядом с полем «Папка для результата» (опционально)
- [ ] Открывает папку `generated/` в проводнике

## Зависимости

- Требуется endpoint `/api/open-file` из задачи [Интерактивный список файлов](task-ux-interactive-file-list.md)
- Если та задача не выполнена — нужно создать endpoint `/api/open-file` в рамках этой задачи

## Связанные файлы

- `src/word_template_generator/web/static/index.html` — кнопка «Открыть шаблон»
- `src/word_template_generator/web/static/app.js` — `openTemplate()`
- `src/word_template_generator/web/routes.py` — `/api/template-path` или расширение `/api/acts`
- `src/word_template_generator/web/schemas.py` — payload если нужен

## Связанные задачи

- [Интерактивный список файлов](task-ux-interactive-file-list.md) — переиспользование `/api/open-file`

## Оценка

- **Сложность**: 🟢 Низкая
- **Время**: ~1-2 часа
- Большая часть инфраструктуры (endpoint открытия файлов) реализуется в задаче с интерактивным списком
