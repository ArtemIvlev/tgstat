import asyncio
import os
from dotenv import load_dotenv
from tgstats.database import Database
from tgstats.client import get_client
from tgstats.collectors import PostCommentsCollector
from tgstats.config.config import CHANNEL_IDS, CHANNEL_USERNAME
from tgstats.logger import get_logger

# Загружаем переменные окружения
load_dotenv()

# Создаем логгер
logger = get_logger(__name__)

async def collect_comments(client, db, channel):
    """Сбор комментариев для одного канала"""
    try:
        # Определяем канал
        if isinstance(channel, str) and channel.isdigit():
            logger.info(f"Используется ID канала: {channel}")
            channel_id = int(channel)
            channel_peer = channel_id
        else:
            logger.info(f"Используется юзернейм канала: {channel}")
            channel_peer = channel
        
        # Создаем и запускаем коллектор комментариев
        collector = PostCommentsCollector(client, db)
        logger.info(f"Запуск сбора комментариев для канала {channel}")
        await collector.run(channel_peer)
        logger.info(f"Сбор комментариев успешно завершен для канала {channel}")
                
    except Exception as e:
        logger.error(f"Ошибка при сборе комментариев для канала {channel}: {str(e)}", exc_info=True)

async def main():
    logger.info("Запуск сбора комментариев")
    
    # Инициализируем клиент Telegram
    logger.info("Инициализация клиента Telegram")
    client = get_client()
    await client.start()
    
    # Инициализируем базу данных
    logger.info("Инициализация базы данных")
    db = Database()
    
    try:
        # Собираем комментарии для каждого канала
        channels = CHANNEL_IDS if CHANNEL_IDS else [CHANNEL_USERNAME]
        for channel in channels:
            await collect_comments(client, db, channel)
            
    finally:
        logger.info("Отключение клиента Telegram")
        await client.disconnect()
        logger.info("Сбор комментариев завершен")

if __name__ == "__main__":
    asyncio.run(main()) 