import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DB_PATH = ROOT_DIR / "data" / "bot.sqlite3"
CONTENT_DIR = Path(__file__).resolve().parent / "content"
SEED_YAML = CONTENT_DIR / "seed.yaml"
ANSWERS_DIR = CONTENT_DIR / "answers"
IMAGES_DIR = ROOT_DIR / "assets" / "images"

# Позже: список Telegram user id. Пока is_admin() всегда True.
_ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "").strip()
ADMIN_IDS: set[int] = {
    int(part.strip())
    for part in _ADMIN_IDS_RAW.split(",")
    if part.strip().isdigit()
}
