# RoyalVPN Project

## Telegram Bot Integration

This repo now includes:

- `botapi/`: Django-side secure API for the Telegram bot
- `telegram_bot/`: aiogram 3 runner that talks to the Django API

### Required environment variables

- `BOT_API_KEY`
- `BOT_API_SECRET`
- `BOT_TOKEN`
- `BOT_API_BASE_URL`
- `BOT_ADMIN_TELEGRAM_IDS` (comma-separated Telegram user IDs for admins)

Optional:

- `BOT_ALLOWED_IPS`
- `BOT_SESSION_TTL_HOURS`
- `BOT_SIGNATURE_WINDOW_SECONDS`
- `BOT_REQUEST_TIMEOUT`

### Run the bot

```bash
python -m telegram_bot.main
```
