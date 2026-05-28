# Архитектура проекта Codely

**Codely** — веб-приложение для совместной работы с учебными конспектами. Пользователи создают заметки, редактируют их в реальном времени, объединяются в группы, добавляют друзей, публикуют материалы и оценивают работу друг друга.

Документ описывает архитектуру системы для курсовой работы. Диаграммы находятся в каталоге [`diagrams/`](./diagrams/).

| Файл | Тип диаграммы | Назначение |
|------|---------------|------------|
| [`01-flowchart-user-journey.mmd`](./diagrams/01-flowchart-user-journey.mmd) | Flowchart TD | Пользовательские сценарии |
| [`02-sequence-realtime-collaboration.mmd`](./diagrams/02-sequence-realtime-collaboration.mmd) | Sequence | Совместное редактирование |
| [`03-er-database.mmd`](./diagrams/03-er-database.mmd) | ER-диаграмма | Модель данных PostgreSQL |
| [`04-flowchart-system-components.mmd`](./diagrams/04-flowchart-system-components.mmd) | Flowchart TD | Компоненты и инфраструктура |

---

## 1. Общая архитектура

Система построена по классической трёхуровневой схеме **клиент — сервер — данные** и разворачивается через **Docker Compose**.

```
Браузер (Vue 3 SPA)
        │
        ▼
   Nginx :80  ── статика + reverse proxy
        │
        ├── /api/*  →  FastAPI :8000
        ├── /ws/*   →  FastAPI WebSocket
        └── /*      →  frontend/dist (SPA)
                │
                ├── PostgreSQL 16  (основное хранилище)
                └── Redis 7        (pub/sub для realtime)
```

**Принципы:**

- **Единая точка входа** — Nginx принимает HTTP и WebSocket, проксирует API и отдаёт собранный frontend.
- **REST API** — бизнес-логика (авторизация, конспекты, группы, друзья) реализована в FastAPI.
- **Realtime** — отдельный WebSocket-канал для синхронизации текста; Redis обеспечивает масштабирование между несколькими инстансами backend.
- **Контейнеризация** — все сервисы описаны в `docker-compose.yml`, что упрощает развёртывание и передачу проекта.

---

## 2. Клиентская часть (Frontend)

**Стек:** Vue 3, Vite, Vue Router.

### Структура

| Каталог / файл | Назначение |
|----------------|------------|
| `frontend/src/views/` | Страницы приложения |
| `frontend/src/components/RichEditor.vue` | WYSIWYG-редактор на TipTap |
| `frontend/src/api/client.js` | HTTP-клиент к REST API |
| `frontend/src/state/auth.js` | Состояние авторизации |
| `frontend/src/router/index.js` | Маршрутизация и guard'ы |

### Маршруты

| Путь | Компонент | Доступ |
|------|-----------|--------|
| `/login` | LoginView | Только гости |
| `/cabinet` | CabinetView | Авторизованные |
| `/groups` | GroupsView | Авторизованные |
| `/friends` | FriendsView | Авторизованные |
| `/notes/new` | NoteWizardView | Авторизованные |
| `/notes/:id` | NoteDetailView | Авторизованные |
| `/users/:login` | UserNotesView | Авторизованные |

Router guard (`beforeEach`) вызывает `auth.initAuth()` и перенаправляет неавторизованных пользователей на `/login`.

### Редактор конспектов

Редактор построен на **TipTap + Yjs + Collaboration**:

- между клиентами передаются инкрементальные CRDT-апдейты (`yjs_update`), а не весь HTML;
- периодически отправляется снапшот состояния Yjs для надёжной персистентности;
- через **awareness** отображаются курсоры и выделения участников;
- при отключении клиента его курсор удаляется у остальных участников.

---

## 3. Серверная часть (Backend)

**Стек:** Python 3, FastAPI, SQLAlchemy (async), Pydantic.

### Точка входа

`backend/app/main.py`:

- создаёт таблицы БД при старте (`Base.metadata.create_all`);
- выполняет seed предметов (`seed_subjects`);
- подключает REST-роутер (`/api`) и WebSocket-роутер (`/ws`).

### Слои приложения

```
API Routes  →  Services  →  Models (SQLAlchemy)  →  PostgreSQL
     ↓
  Schemas (Pydantic) — валидация запросов/ответов
     ↓
  deps.py — dependency injection (сессия БД, текущий пользователь)
```

| Слой | Каталог | Описание |
|------|---------|----------|
| Маршруты | `app/api/routes/` | HTTP-эндпоинты по доменам |
| Схемы | `app/schemas/` | DTO для API |
| Сервисы | `app/services/` | Бизнес-логика |
| Модели | `app/models/` | ORM-сущности |
| WebSocket | `app/ws/` | Realtime-синхронизация |
| Политики | `app/services/access_policy.py` | Проверка прав доступа |

### REST API (основные группы)

| Префикс | Функциональность |
|---------|------------------|
| `/api/auth` | Регистрация, вход, выход, текущий пользователь |
| `/api/notes` | CRUD конспектов, публикация, ревизии |
| `/api/groups` | Группы, заявки на вступление, участники |
| `/api/friends` | Заявки в друзья, список друзей |
| `/api/users` | Поиск пользователей, их публичные конспекты |
| `/api/subjects` | Справочник учебных предметов |
| `/api/cabinet` | Агрегированные данные личного кабинета |
| `/api/health` | Health-check |

### Авторизация

Используется **сессионная модель** на основе cookie:

1. При входе (`POST /api/auth/login`) сервер создаёт запись в таблице `sessions` и устанавливает HttpOnly-cookie `session_id`.
2. Защищённые эндпoинты получают пользователя через `get_current_user` (зависимость FastAPI).
3. WebSocket также проверяет cookie перед принятием соединения.
4. Сессии имеют ограничения по времени простоя (`SESSION_IDLE_MINUTES`) и максимальному сроку жизни (`SESSION_MAX_DAYS`).

---

## 4. Realtime-синхронизация

WebSocket-эндпoинт: `WS /ws/notes/{note_id}`.

### Компоненты

| Компонент | Файл | Роль |
|-----------|------|------|
| WebSocket handler | `app/ws/routes.py` | Приём/отправка сообщений |
| CollaborationHub | `app/ws/collaboration.py` | Комнаты по note_id, broadcast |
| Redis pub/sub | через `CollaborationHub` | Синхронизация между инстансами API |

### Типы сообщений

| Тип | Направление | Описание |
|-----|-------------|----------|
| `content_sync` | Сервер → клиент | Начальное состояние документа |
| `yjs_update` | Клиент ↔ сервер ↔ клиенты | CRDT-апдейт Yjs |
| `awareness_update` | Клиент ↔ клиенты | Курсоры и выделения |
| `awareness_remove` | Сервер → клиенты | Удаление курсора при disconnect |
| `presence` | Сервер → клиенты | Список участников комнаты |
| `content_saved` | Сервер → клиент | Подтверждение сохранения в БД |

### Хранение контента

В таблице `notes` хранятся два представления:

- `content_yjs` — бинарное CRDT-состояние (для синхронизации);
- `content_html` — HTML-представление (для отображения, ревизий и fallback).

---

## 5. Модель данных

Основные сущности (подробнее — ER-диаграмма `03-er-database.mmd`):

| Сущность | Описание |
|----------|----------|
| `users` | Пользователи системы |
| `sessions` | Серверные сессии авторизации |
| `groups`, `group_memberships` | Группы и членство (с заявками) |
| `friendships` | Связи «друзья» со статусами |
| `subjects` | Справочник предметов |
| `notes` | Конспекты с метаданными и контентом |
| `note_tags` | Теги конспектов |
| `note_comments` | Комментарии к опубликованным конспектам |
| `note_ratings` | Оценки конспектов (1 оценка на пользователя) |
| `note_revisions` | История версий HTML-контента |

Связи построены с каскадным удалением там, где дочерние записи не имеют смысла без родителя (например, комментарии при удалении конспекта).

---

## 6. Инфраструктура и развёртывание

### Docker Compose-сервисы

| Сервис | Образ / сборка | Порт | Назначение |
|--------|----------------|------|------------|
| `postgres` | postgres:16-alpine | 5432 (внутренний) | Основная БД |
| `redis` | redis:7-alpine | 6379 (внутренний) | Pub/sub для realtime |
| `api` | `./backend/Dockerfile` | 8000 (внутренний) | FastAPI backend |
| `nginx` | `./nginx/Dockerfile` | **80** (внешний) | Reverse proxy + статика |

### Nginx

Конфигурация (`nginx/nginx.conf`):

- `/api/*` → прокси на `api:8000`;
- `/ws/*` → WebSocket upgrade на `api:8000`;
- `/docs`, `/redoc`, `/openapi.json` → документация FastAPI;
- `/*` → SPA (`try_files ... /index.html`).

### Переменные окружения

Пример — `.env.example`. Ключевые параметры:

- подключение к PostgreSQL и Redis;
- настройки сессий (cookie, TTL);
- регулярные выражения для валидации логина и пароля.

---

## 7. Безопасность и контроль доступа

- Пароли хранятся в виде хеша (не в открытом виде).
- Session cookie: `HttpOnly`, настраиваемые `Secure` и `SameSite`.
- WebSocket закрывается с кодом `1008`, если нет сессии или нет прав редактирования.
- `AccessPolicy` и `NoteService.can_edit_note()` определяют, кто может читать и редактировать конспект (владелец, участник группы, друг и т.д.).
- Входящие WebSocket-сообщения валидируются по типу и размеру payload.

---

## 8. Технологический стек (сводка)

| Уровень | Технологии |
|---------|------------|
| Frontend | Vue 3, Vite, Vue Router, TipTap, Yjs |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic |
| База данных | PostgreSQL 16 |
| Кэш / pub-sub | Redis 7 |
| Reverse proxy | Nginx |
| Контейнеризация | Docker, Docker Compose |

---

## 9. Как просмотреть диаграммы

Файлы `.mmd` — это исходники [Mermaid](https://mermaid.js.org/). Их можно открыть:

- в VS Code / Cursor с расширением Mermaid Preview;
- на [mermaid.live](https://mermaid.live) (вставить содержимое файла);
- в GitHub/GitLab (Mermaid рендерится в Markdown-блоках).

Пример вставки в Markdown:

````markdown
```mermaid
<!-- содержимое файла 01-flowchart-user-journey.mmd без первой строки-комментария -->
```
````
