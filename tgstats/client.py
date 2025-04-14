from telethon import TelegramClient
from tgstats.config.config import API_ID, API_HASH, SESSION_PATH

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
