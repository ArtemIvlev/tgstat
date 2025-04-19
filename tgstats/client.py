import os
import shutil
from tgstats.telegram.client import TelegramClient
from tgstats.config.config import API_ID, API_HASH, SESSION_PATH
from tgstats.logger import get_logger

logger = get_logger('client')

def get_session_file():
    """
    Проверяет наличие локального файла сессии и при необходимости копирует его из SESSION_PATH
    
    Returns:
        str: Путь к файлу сессии для использования
    """
    local_session = 'tg-post.session'
    
    # Проверяем наличие локального файла сессии
    if os.path.exists(local_session):
        logger.info(f"Найден локальный файл сессии: {local_session}")
        return local_session
    
    # Если локального файла нет, проверяем SESSION_PATH
    if os.path.exists(SESSION_PATH):
        logger.info(f"Копируем файл сессии из {SESSION_PATH} в {local_session}")
        try:
            shutil.copy2(SESSION_PATH, local_session)
            logger.info("Файл сессии успешно скопирован")
            return local_session
        except Exception as e:
            logger.error(f"Ошибка при копировании файла сессии: {str(e)}")
            return SESSION_PATH
    
    logger.info(f"Файл сессии не найден, будет создан новый: {local_session}")
    return local_session

def get_client():
    """
    Возвращает клиент Telegram
    """
    session_file = get_session_file()
    logger.info(f"Создание клиента Telegram с сессией: {session_file}")
    return TelegramClient(session_file, API_ID, API_HASH)
