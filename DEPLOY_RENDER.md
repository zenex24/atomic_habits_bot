## Backend deployment (Render)

1. Откройте Render -> New -> Blueprint.
2. Выберите репозиторий `zenex24/atomic_habits_bot`.
3. Render подхватит `render.yaml` автоматически.
4. После создания сервиса зайдите в Environment и заполните секреты:
   - `BOT_TOKEN`
   - `OPENROUTER_API_KEY`
   - `ADMIN_PANEL_TOKEN` (любой сложный)
   - `WEBAPP_URL=https://zenex24.github.io/atomic_habits_bot/frontend/index.html`
5. Дождитесь первого деплоя и скопируйте URL сервиса:
   - `https://atomic-habits-backend.onrender.com`
6. В Environment добавьте:
   - `PUBLIC_API_BASE=https://atomic-habits-backend.onrender.com`
7. Нажмите Manual Deploy -> Deploy latest commit.
8. В Telegram отправьте `/start` и откройте mini app кнопкой.

Проверка:
- `https://<render-url>/health` возвращает `{"ok": true}`.
- В сообщении `/start` ссылка должна содержать `auth_token=...&api_base=https://<render-url>`.

Важно:
- GitHub Pages без backend дает 404 на `/api/*`.
- На free-плане Render может уходить в sleep, первый запрос после простоя медленный.
