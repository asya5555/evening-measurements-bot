# Deploy to Render

The repository includes `render.yaml`. Render can create the web service and PostgreSQL database from this Blueprint.

1. Push this repository to GitHub.
2. In Render, choose **New > Blueprint**.
3. Connect the GitHub repository.
4. Render reads `render.yaml` and creates:
   - `evening-measurements-bot`
   - `evening-measurements-db`
5. Fill only secret fields:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_ALLOWED_USER_IDS` or `TELEGRAM_ALLOWED_USERNAMES`
   - `OPENAI_API_KEY`
6. Deploy.

The app runs migrations with `alembic upgrade head` before deploy and sets the Telegram webhook on startup when `AUTO_SET_WEBHOOK=true`.

Rollback: redeploy the previous Render image/version and restore PostgreSQL from the latest Render backup if the migration changed data irreversibly.

Backups: enable daily Render PostgreSQL backups. Media is intentionally temporary; keep persistent disk only if you choose to retain media longer than `MEDIA_RETENTION_DAYS`.
