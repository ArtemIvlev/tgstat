import logging
import os
from logging.handlers import RotatingFileHandler
from tgstats.config.logging_config import (
    LOG_DIR, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT,
    LOG_FILE_PATH, LOG_MAX_BYTES, LOG_BACKUP_COUNT,
    MODULE_LOG_LEVELS, CONSOLE_LOG_LEVEL, CONSOLE_LOG_FORMAT
)

# Создаем директорию для логов, если она не существует
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Настраиваем корневой логгер
def setup_logging():
    """
    Настраивает систему логирования
    """
    # Получаем корневой логгер
    root_logger = logging.getLogger('tgstats')
    
    # Устанавливаем уровень логирования
    root_logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Очищаем существующие обработчики
    root_logger.handlers = []
    
    # Создаем обработчик для файла с ротацией
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    
    # Создаем обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, CONSOLE_LOG_LEVEL))
    console_handler.setFormatter(logging.Formatter(CONSOLE_LOG_FORMAT, LOG_DATE_FORMAT))
    
    # Добавляем обработчики к корневому логгеру
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Настраиваем уровни логирования для разных модулей
    for module, level in MODULE_LOG_LEVELS.items():
        module_logger = logging.getLogger(module)
        module_logger.setLevel(getattr(logging, level))
    
    # Отключаем логи от библиотек
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

# Инициализируем логирование
setup_logging()

# Создаем логгер для нашего приложения
logger = logging.getLogger('tgstats')

def get_logger(name):
    """
    Возвращает логгер с указанным именем
    """
    return logging.getLogger(f'tgstats.{name}') 