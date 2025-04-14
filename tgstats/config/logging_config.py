import os
from datetime import datetime
import logging
from .config import LOG_LEVEL, LOG_FORMAT, LOG_FILE

# Базовые настройки логирования
LOG_DIR = 'logs'
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Настройки файлов логов
LOG_FILENAME_PREFIX = 'tgstats'
LOG_FILENAME_DATE_FORMAT = '%Y%m%d'
LOG_FILENAME = f'{LOG_FILENAME_PREFIX}_{datetime.now().strftime(LOG_FILENAME_DATE_FORMAT)}.log'
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILENAME)

# Настройки ротации логов
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Настройки для разных модулей
MODULE_LOG_LEVELS = {
    'tgstats': LOG_LEVEL,
    'tgstats.collectors': LOG_LEVEL,
    'tgstats.database': LOG_LEVEL,
    'tgstats.analyze': LOG_LEVEL,
}

# Настройки для вывода в консоль
CONSOLE_LOG_LEVEL = LOG_LEVEL
CONSOLE_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

def get_logging_config():
    """
    Возвращает конфигурацию логирования
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': LOG_FORMAT
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': LOG_LEVEL,
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': LOG_FILE,
                'formatter': 'standard',
                'level': LOG_LEVEL,
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console', 'file'],
                'level': LOG_LEVEL,
                'propagate': True
            }
        }
    } 