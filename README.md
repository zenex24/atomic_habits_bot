# Atomic Habits Telegram Bot + Mini App

Локальный проект на Python:
- `aiogram` бот
- `FastAPI` backend API
- `SQLite` база
- mini app (статический фронт, совместим с GitHub Pages)
- чат-наставник через OpenRouter

## Функции
- Онбординг при первом входе (имя, цель, привычка, детали, тон, время напоминания, согласие)
- 5 вкладок mini app: Главная, Чат, План, Челленджи, Профиль
- Память чата по пользователю
- Лимит сообщений в день
- Ежедневные напоминания 1 раз в день по локальному часовому поясу
- Админ-панель с метриками и списком пользователей

## Запуск локально
1. Создайте и активируйте виртуальное окружение.
2. Установите зависимости:
```bash
pip install -r requirements.txt
```
3. Создайте `.env` на основе `.env.example` и заполните:
- `BOT_TOKEN`
- `OPENROUTER_API_KEY`
- `ADMIN_PANEL_TOKEN`
- `WEBAPP_URL`

4. Запуск:
```bash
python run.py
```

Сервер поднимется на `http://localhost:8000`.
`run.py` автоматически:
- подтянет `.env`
- если `WEBAPP_URL` локальный/пустой и запущен `ngrok`, подхватит публичный HTTPS URL
- выставит `PUBLIC_API_BASE`
- обновит `frontend/assets/config.js` (`API_BASE`)
- настроит у бота кнопку меню Mini App

## Telegram Mini App
1. Создайте бота через BotFather.
2. Включите Web App кнопку (у нас она отдается в `/start`).
3. Для локального открытия mini app через Telegram используйте туннель (например, `ngrok`) и выставьте `WEBAPP_URL` на HTTPS URL туннеля.
4. Напишите боту `/start` и откройте mini app через кнопку.

## Admin panel
- Открывается по `http://localhost:8000/admin.html?token=ВАШ_ADMIN_PANEL_TOKEN`

## Деплой фронта на GitHub Pages
1. Убедитесь, что основная ветка называется `main`.
2. В `frontend/assets/config.js` укажите публичный URL вашего backend в `API_BASE`.
3. Запушьте изменения в GitHub.
4. Workflow `.github/workflows/deploy-pages.yml` автоматически задеплоит папку `frontend/` на Pages.
5. Итоговый URL будет вида: `https://<username>.github.io/<repo>/`.

## Подключение в BotFather
1. Откройте `@BotFather` -> `/mybots` -> ваш бот -> `Bot Settings` -> `Menu Button`.
2. Поставьте Web App URL = URL GitHub Pages.
3. В `.env` backend укажите:
- `WEBAPP_URL=https://<username>.github.io/<repo>/`

## Быстрый deploy backend на Render
- Инструкция: `DEPLOY_RENDER.md`
- Конфиг Blueprint: `render.yaml`
- Важный env для автосборки ссылки mini app: `PUBLIC_API_BASE=https://<your-render-url>`
