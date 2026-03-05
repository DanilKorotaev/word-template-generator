# Задача: Лоадеры на кнопках при выполнении операций

**Статус**: 📋 Запланировано  
**Приоритет**: 🔴 Высокий  
**Категория**: Улучшения UX

## Описание

Сейчас при нажатии на любую кнопку (Проверить, Сгенерировать, Загрузить, Выбрать папку) нет никакого визуального фидбэка, что запрос принят и обрабатывается. На слабых машинах (особенно Windows-ноутбуки) операции могут занимать несколько секунд, и пользователь не понимает:
- Нажалась ли кнопка?
- Идёт ли процесс?
- Не зависло ли приложение?

Это приводит к повторным нажатиям и негативному UX.

## Проблема

Все async-функции в `app.js` выполняют `fetch()` без блокировки UI:

```javascript
async function buildAll() {
  // ...нет индикации начала...
  const res = await fetch("/api/build-all", { ... });
  // ...индикация только после завершения...
}
```

Кнопки остаются активными, визуально ничего не меняется до завершения запроса.

## Решение

### Подход: обёртка `withLoading(button, asyncFn)`

Универсальная обёртка, которая:
1. Дизейблит кнопку
2. Добавляет CSS-класс `loading` (показывает спиннер)
3. Сохраняет оригинальный текст
4. По завершении — восстанавливает состояние

```javascript
async function withLoading(buttonOrEvent, asyncFn) {
  const btn = buttonOrEvent instanceof Event
    ? buttonOrEvent.currentTarget
    : buttonOrEvent;
  
  btn.disabled = true;
  btn.classList.add("loading");
  const originalText = btn.textContent;
  
  try {
    await asyncFn();
  } finally {
    btn.disabled = false;
    btn.classList.remove("loading");
    btn.textContent = originalText;
  }
}
```

### CSS-спиннер

```css
button.loading {
  position: relative;
  color: transparent;
  pointer-events: none;
}

button.loading::after {
  content: "";
  position: absolute;
  width: 16px;
  height: 16px;
  top: 50%;
  left: 50%;
  margin: -8px 0 0 -8px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

### Применение ко всем кнопкам

Два подхода:

**A. Inline onclick с обёрткой:**
```html
<button onclick="withLoading(event, buildAll)">Сгенерировать все</button>
```

**B. Data-атрибуты + автоматическая привязка:**
```html
<button data-action="buildAll">Сгенерировать все</button>
```
```javascript
document.querySelectorAll("[data-action]").forEach(btn => {
  const fn = window[btn.dataset.action];
  btn.addEventListener("click", (e) => withLoading(e, fn));
});
```

## Задачи

### 1. Создать CSS для состояния loading

- [ ] Добавить стили `.loading` в `style.css`
- [ ] Спиннер через `::after` псевдоэлемент
- [ ] Анимация `spin` (rotate 360deg)
- [ ] Текст кнопки скрывается (`color: transparent`), размер кнопки не меняется
- [ ] Для `.secondary.loading` — адаптировать цвета спиннера

### 2. Создать JS-обёртку `withLoading()`

- [ ] Функция принимает кнопку (или Event) и async-функцию
- [ ] Дизейблит кнопку, добавляет `.loading`
- [ ] В `finally` — восстанавливает состояние (даже при ошибке)
- [ ] Защита от повторного вызова (если уже loading — игнорировать)

### 3. Обернуть все async-кнопки

Кнопки, которые нужно обернуть:

- [ ] `pickFolder()` — «Выбрать папку...»
- [ ] `loadActs()` — «Загрузить»
- [ ] `validateWs()` — «Проверить»
- [ ] `buildAll()` — «Сгенерировать все»
- [ ] `buildOne()` — «Сгенерировать выбранный»

### 4. Синхронные кнопки (опционально)

Для синхронных операций лоадер не нужен, но кнопки можно кратковременно анимировать:

- [ ] `useRecent()`, `removeRecent()`, `clearRecent()` — мгновенные, не нужен лоадер
- [ ] `clearLog()` — мгновенный, не нужен лоадер

### 5. Обработка сетевых ошибок

- [ ] Обернуть `fetch()` в `try/catch` во всех async-функциях
- [ ] При сетевой ошибке: показать toast + снять лоадер
- [ ] Сейчас сетевые ошибки (сервер не отвечает) приводят к uncaught promise rejection

## Технические детали

- Спиннер реализован чисто на CSS (без дополнительных иконок или SVG)
- Размер кнопки фиксируется при loading через `min-width` или сохранение текста
- `pointer-events: none` предотвращает повторные нажатия даже если `disabled` не сработает
- `finally` гарантирует снятие лоадера при любом исходе

## Связанные файлы

- `src/word_template_generator/web/static/style.css` — стили `.loading`, анимация
- `src/word_template_generator/web/static/app.js` — `withLoading()`, обёртка всех кнопок
- `src/word_template_generator/web/static/index.html` — обновление `onclick` атрибутов

## Оценка

- **Сложность**: 🟢 Низкая
- **Время**: ~2-3 часа
- Простая задача, но затрагивает все кнопки — нужно аккуратно протестировать каждую
