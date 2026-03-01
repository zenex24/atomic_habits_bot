## Backend deployment (Render)

1. Откройте Render -> New -> Blueprint.
2. Выберите репозиторий `zenex24/atomic_habits_bot`.
3. Render подхватит файл `render.yaml` автоматически.
4. После создания сервиса зайдите в Environment и заполните секреты:
   - `BOT_TOKEN`
   - `OPENROUTER_API_KEY`
   - `ADMIN_PANEL_TOKEN` (любой сложный)
5. Дождитесь первого деплоя и скопируйте URL сервиса, например:
   - `https://atomic-habits-backend.onrender.com`
6. В том же Environment обновите `WEBAPP_URL`:
   - `https://zenex24.github.io/atomic_habits_bot/frontend/index.html?api_base=https://atomic-habits-backend.onrender.com`
7. Нажмите Manual Deploy -> Deploy latest commit.
8. В Telegram откройте бота и отправьте `/start`, затем нажмите кнопку mini app.

Проверка:
- `https://<render-url>/health` должен вернуть `{"ok": true}`.

Важно:
- GitHub Pages без backend всегда дает 404 на `/api/*`.
- Если Telegram снова кэширует фронт, откройте /start заново и используйте новую кнопку.
