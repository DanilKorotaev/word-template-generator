# Документация Word Template Generator

## Содержание

- `USER_GUIDE_RU.md` — инструкция для конечного пользователя.
- `OPERATOR_CHECKLIST_RU.md` — короткий ежедневный чеклист.
- `DEV_GUIDE_RU.md` — техническое руководство для поддержки и разработки.
- `RELEASE_CHECKLIST_RU.md` — чеклист перед релизом.
- `GIT_FLOW_RU.md` — правила ветвления и релизов по GitFlow.
- `WINDOWS_SETUP_RU.md` — подробная установка и запуск на Windows.
- `DEPLOYMENT_SERVER_RU.md` — опциональный серверный деплой (future-track).

## Быстрый старт разработки

1. Установить зависимости: `pip install -e .`
2. Запустить UI: `word-gen web-ui`
3. Проверить работу на demo-workspace.

## Политика процесса

- Для разработки и релизов используется GitFlow.
- Для сообщений коммитов используется Conventional Commits.
- Требования к процессу также закреплены в `agent/system_prompt.md`.
