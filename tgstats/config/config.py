import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Config:
    def __init__(self):
        # Telegram API credentials
        self.API_ID = os.getenv('TG_API_ID')
        self.API_HASH = os.getenv('TG_API_HASH')

        # Session configuration
        self.SESSION_PATH = os.getenv('SESSION_PATH', 'tgstats.session')

        # Channel configuration
        channel_ids = os.getenv('TG_CHANNEL_IDS', '').split(',') if os.getenv('TG_CHANNEL_IDS') else []
        self.CHANNEL_IDS = [int(id.strip()) for id in channel_ids if id.strip()]

        # Юзернейм канала (если ID не указан)
        self.CHANNEL_USERNAME = os.getenv('TG_CHANNEL_USERNAME', '')

        # Проверяем, что хотя бы один идентификатор канала указан
        if not self.CHANNEL_IDS and not self.CHANNEL_USERNAME:
            raise ValueError("Необходимо указать TG_CHANNEL_IDS или TG_CHANNEL_USERNAME в .env файле")

        # Channel configuration
        self.CHANNEL_ID = os.getenv('TG_CHANNEL_ID')
        self.CHANNEL_TITLE = os.getenv('TG_CHANNEL_TITLE', 'Unknown Channel')

        # Logging configuration
        self.LOG_LEVEL = os.getenv("TG_LOG_LEVEL", "INFO")
        self.LOG_FORMAT = os.getenv("TG_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.LOG_FILE = os.getenv("TG_LOG_FILE", "tgstats.log")

        # Параметры PostgreSQL
        self.POSTGRES_HOST = os.getenv('POSTGRES_HOST', '')
        self.POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
        self.POSTGRES_DB = os.getenv('POSTGRES_DB', 'DB')
        self.POSTGRES_USER = os.getenv('POSTGRES_USER', '')
        self.POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')

        self.TABLE_NAME = os.getenv('TABLE_NAME', "tgstat")

        # Параметры подключения к PostgreSQL в виде словаря
        self.PG_CONNECTION_PARAMS = {
            'host': self.POSTGRES_HOST,
            'port': self.POSTGRES_PORT,
            'database': self.POSTGRES_DB,
            'user': self.POSTGRES_USER,
            'password': self.POSTGRES_PASSWORD
        }

# Для обратной совместимости
API_ID = os.getenv('TG_API_ID')
API_HASH = os.getenv('TG_API_HASH')
SESSION_PATH = os.getenv('SESSION_PATH', 'tgstats.session')
CHANNEL_IDS = [int(id.strip()) for id in os.getenv('TG_CHANNEL_IDS', '').split(',') if id.strip()]
CHANNEL_USERNAME = os.getenv('TG_CHANNEL_USERNAME', '')
CHANNEL_ID = os.getenv('TG_CHANNEL_ID')
CHANNEL_TITLE = os.getenv('TG_CHANNEL_TITLE', 'Unknown Channel')
LOG_LEVEL = os.getenv("TG_LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("TG_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_FILE = os.getenv("TG_LOG_FILE", "tgstats.log")
PG_CONNECTION_PARAMS = {
    'host': os.getenv('POSTGRES_HOST', ''),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'DB'),
    'user': os.getenv('POSTGRES_USER', ''),
    'password': os.getenv('POSTGRES_PASSWORD', '')
}

__all__ = [
    'Config',
    'API_ID',
    'API_HASH',
    'SESSION_PATH',
    'CHANNEL_USERNAME',
    'CHANNEL_ID',
    'CHANNEL_TITLE',
    'LOG_LEVEL',
    'LOG_FORMAT',
    'LOG_FILE',
    'PG_CONNECTION_PARAMS'
] 