# Codely

Веб-приложение для совместной работы с конспектами.

## Что есть в проекте

- `backend/` — FastAPI API, авторизация и сессии.
- `frontend/` — Vue 3 (Vite), клиентская часть.
- `nginx/` — reverse proxy и раздача frontend.
- `docker-compose.yml` — запуск всех сервисов одной командой.
- `.env.example` — пример переменных окружения.

## Сервисы

- `postgres` — основная база данных.
- `redis` — инфраструктурный сервис для realtime-задач.
- `api` — backend на FastAPI.
- `nginx` — внешний вход (`http://localhost`), проксирует `/api`.

## Запуск проекта (рекомендуется, через Docker)

1. Установите Docker Desktop (Windows/macOS) или Docker Engine + Compose (Linux).
2. В корне проекта создайте `.env` из примера:
  - Windows (PowerShell): `Copy-Item .env.example .env`
  - Linux/macOS: `cp .env.example .env`
3. Запустите проект:
  - `docker compose up -d --build`
4. Проверьте, что всё поднялось:
  - `docker compose ps`
5. Откройте:
  - приложение: `http://localhost`
  - документация API: `http://localhost/docs`
  - health-check API: `http://localhost/api/health`

## Полезные команды

- Остановить: `docker compose down`
- Остановить и удалить тома БД/Redis: `docker compose down -v`
- Посмотреть логи: `docker compose logs -f`
- Пересобрать после изменений: `docker compose up -d --build`

## Основные API эндпоинты

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/subjects`
- `POST /api/notes`
- `GET /api/notes`
- `GET /api/notes/public` — лента опубликованных публичных конспектов
- `GET /api/notes/{note_id}`
- `PATCH /api/notes/{note_id}`
- `DELETE /api/notes/{note_id}`
- `POST /api/notes/{note_id}/publish`
- `GET /api/notes/{note_id}/comments`
- `POST /api/notes/{note_id}/comments`
- `GET /api/notes/{note_id}/rating`
- `PUT /api/notes/{note_id}/rating`
- `GET /api/notes/{note_id}/revisions`
- `POST /api/notes/{note_id}/revisions`
- `POST /api/notes/{note_id}/revisions/{revision_id}/restore`
- `WS /ws/notes/{note_id}` (realtime sync текста)
- `GET /api/cabinet`
- `POST /api/groups`
- `GET /api/groups/mine`
- `POST /api/groups/join-request`
- `GET /api/groups/{group_id}/requests/incoming` — входящие заявки (только владелец группы)
- `PATCH /api/groups/{group_id}/requests/{user_id}` — принять или отклонить заявку
- `POST /api/groups/{group_id}/leave` — выйти из группы
- `GET /api/groups/{group_id}/members`
- `GET /api/groups/{group_id}/notes`
- `POST /api/friends/request`
- `GET /api/friends`
- `GET /api/friends/requests/incoming`
- `PATCH /api/friends/requests/{request_id}`
- `DELETE /api/friends/{user_id}` — удалить из друзей
- `GET /api/users/search?q=login_prefix`
- `GET /api/users/{login}/notes`
- `GET /api/health`

## Передача проекта коллеге

Передавайте исходники проекта без локальных артефактов:

- не передавать: `.venv/`, `node_modules/`, `frontend/dist/`, `__pycache__/`, `.env`
- передавать: код, `docker-compose.yml`, `.env.example`, `README.md`

## Realtime заметки

- WebSocket синхронизация работает через `WS /ws/notes/{note_id}`.
- Для масштабирования между несколькими backend-инстансами используется Redis pub/sub.

### Как сейчас работает realtime

- Редактор использует `Yjs + TipTap Collaboration`.
- Между клиентами передаются инкрементальные CRDT-апдейты (`yjs_update`), а не весь HTML.
- Периодически отправляется снапшот состояния Yjs для надежной персистентности в БД.
- Сервер хранит:
  - `content_yjs` — бинарное CRDT-состояние (для последующей синхронизации),
  - `content_html` — HTML-представление (для отображения, ревизий и fallback-пути).
- Включен `awareness`:
  - живые курсоры/выделения участников (через `@tiptap/extension-collaboration-cursor`),
  - удаление курсора при дисконнекте пользователя (без "зависших" состояний).

### Что проверить после деплоя

- Откройте один и тот же конспект в двух разных браузерах/аккаунтах.
- Проверьте, что:
  - текст синхронизируется в реальном времени в обе стороны;
  - курсоры и выделения видны у второго участника;
  - после закрытия вкладки курсор пользователя исчезает у остальных;
  - при перезапуске сервисов `docker compose restart api nginx` документ открывается корректно.

