import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
SESSION_PATH = os.getenv("TG_SESSION", "tgstats.session")

# Database configuration
DB_URL = os.getenv("TG_DB_URL", "sqlite:///tgstats.db")

# Channel configuration
CHANNEL_USERNAME = os.getenv("TG_CHANNEL_USERNAME", "homoludens_asia_trip")
CHANNEL_ID = os.getenv("TG_CHANNEL_ID")  # ID для закрытых каналов
CHANNEL_TITLE = os.getenv("TG_CHANNEL_TITLE", "Моё большое путешествие")
