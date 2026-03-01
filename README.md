# Atomic Habits Telegram Mini App (MVP)

Структура:
- `frontend/` - React + Vite Mini App (GitHub Pages)
- `backend/` - FastAPI + aiogram + SQLite + OpenRouter

## Важно
GitHub Pages подходит только для фронтенда (`HTML/CSS/JS`).
Python backend, бот и БД запускаются отдельно.

## Продуктовые правила (зафиксировано)
- Язык: RU
- В онбординге можно выбрать и хорошие, и плохие привычки одновременно
- `Другое` до 300 символов
- Плохие привычки: постепенное снижение -> полный отказ
- Режим наставника: мягкий / нейтральный / строгий
- План: AI, форматы день + неделя
- Напоминания: ежедневно, время меняется в профиле
- Челленджи: 7 / 14 / 30 / без пропусков

## Backend (локально, без Docker)
1. Установи Python `3.11+`.
2. В папке `backend`:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```
3. Заполни `.env`:
- `TELEGRAM_BOT_TOKEN`
- `OPENROUTER_API_KEY`
- `DATABASE_URL` (по умолчанию уже SQLite: `sqlite+aiosqlite:///./atomic_habits.db`)
- `REQUIRE_PAID_ACCESS=true` (в проде)
- `DEV_AUTO_PAID=true` (для локального теста)

4. Запуск API:
```powershell
uvicorn app.main:app --reload --port 8000
```

5. Во втором терминале запуск бота:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m bot.main
```

## Frontend (локально)
```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

URL: `http://127.0.0.1:5173`

## GitHub Pages (только фронтенд)
1. В `frontend/vite.config.js` используется `GITHUB_PAGES_BASE`.
2. Перед билдом задай:
- `GITHUB_PAGES_BASE="/<repo-name>/"`
3. Сборка:
```powershell
cd frontend
npm run build
```
4. Публикуй `frontend/dist`.

## API (MVP)
- `POST /api/v1/auth/telegram-login`
- `POST /api/v1/onboarding`
- `GET /api/v1/profile`
- `PATCH /api/v1/profile`
- `GET /api/v1/profile/stats`
- `POST /api/v1/chat/message`
- `POST /api/v1/plan/generate`
- `GET /api/v1/plan/daily`
- `GET /api/v1/plan/weekly`
- `GET /api/v1/challenges`
- `POST /api/v1/challenges/join`

## Безопасность
- Не храни токены в коде.
- Используй только `.env`.
- Если токены уже утекли, отзови и перевыпусти.
