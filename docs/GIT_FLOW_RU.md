# GitFlow для word-template-generator

## Основные ветки

- `main` — стабильная ветка для релизов.
- `develop` — интеграционная ветка разработки.

## Вспомогательные ветки

- `feature/<name>` — разработка новой функции от `develop`.
- `release/vX.Y.Z` — подготовка релиза от `develop`.
- `hotfix/vX.Y.Z` — срочное исправление от `main`.

## Базовый процесс

### Feature

```bash
git checkout develop
git pull origin develop
git checkout -b feature/recent-projects
# изменения
git add .
git commit -m "feat: add recent projects in web ui"
git push -u origin feature/recent-projects
```

### Release

```bash
git checkout develop
git pull origin develop
git checkout -b release/v0.2.0
# релизные правки
git add .
git commit -m "chore: prepare release v0.2.0"
git push -u origin release/v0.2.0
```

### Hotfix

```bash
git checkout main
git pull origin main
git checkout -b hotfix/v0.2.1
# фикс
git add .
git commit -m "fix: handle invalid workspace path"
git push -u origin hotfix/v0.2.1
```

## Формат коммитов

Используем Conventional Commits:

- `feat:` новая функциональность
- `fix:` исправление ошибки
- `docs:` изменения документации
- `refactor:` рефакторинг без изменения внешнего поведения
- `test:` тесты
- `chore:` служебные изменения

## Правила для этого репозитория

- Нельзя коммитить напрямую в `main`.
- Новые фичи и существенные правки только через `feature/*` от `develop`.
- Любой релиз проходит через `release/*` и теги `vX.Y.Z`.
