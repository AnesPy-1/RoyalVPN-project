import os
from pathlib import Path

from environs import Env


env = Env()
repo_root = Path(__file__).resolve().parents[1]
env.read_env(repo_root / ".env")
local_env = Path(__file__).resolve().with_name(".env")
if local_env.exists():
    env.read_env(local_env)

BOT_TOKEN = env.str("BOT_TOKEN", default="")
BOT_API_BASE_URL = env.str("BOT_API_BASE_URL", default="http://127.0.0.1:8000/api/bot").rstrip("/")
BOT_API_KEY = env.str("BOT_API_KEY", default="")
BOT_API_SECRET = env.str("BOT_API_SECRET", default="")
BOT_ADMIN_TELEGRAM_IDS = {
    item.strip()
    for item in env.str("BOT_ADMIN_TELEGRAM_IDS", default="").split(",")
    if item.strip()
}
BOT_REQUEST_TIMEOUT = env.int("BOT_REQUEST_TIMEOUT", default=20)
