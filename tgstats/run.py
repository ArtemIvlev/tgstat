import asyncio
import os
from dotenv import load_dotenv
from telethon.tl.types import PeerChannel
from tgstats.database import Database
from tgstats.client import get_client
from tgstats.collectors import (
    ChannelStatsCollector,
    ChannelPostsCollector,
    ChannelParticipantsCollector,
    ChannelActivityCollector,
    DiscussionStatsCollector
)
from tgstats.config.config import CHANNEL_IDS, CHANNEL_USERNAME
from tgstats.logger import get_logger

# Загружаем переменные окружения
load_dotenv()

# Создаем логгер
logger = get_logger(__name__)

async def collect_channel_stats(client, db, channel):
    """Сбор статистики для одного канала"""
    try:
        # Определяем канал
        if isinstance(channel, str) and channel.isdigit():
            logger.info(f"Используется ID канала: {channel}")
            channel_id = int(channel)
            channel_peer = channel_id
        else:
            logger.info(f"Используется юзернейм канала: {channel}")
            channel_peer = channel
        
        # Собираем статистику
        collectors = [
            ChannelStatsCollector(client, db),
            ChannelPostsCollector(client, db),
            ChannelParticipantsCollector(client, db),
            ChannelActivityCollector(client, db),
            DiscussionStatsCollector(client, db)
        ]
        
        # Запускаем все коллекторы
        for collector in collectors:
            try:
                logger.info(f"Запуск коллектора {collector.__class__.__name__} для канала {channel}")
                await collector.run(channel_peer)
                logger.info(f"Коллектор {collector.__class__.__name__} успешно завершил работу для канала {channel}")
            except Exception as e:
                logger.error(f"Ошибка в коллекторе {collector.__class__.__name__} для канала {channel}: {str(e)}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Ошибка при сборе статистики для канала {channel}: {str(e)}", exc_info=True)

async def main():
    logger.info("Запуск сбора статистики каналов")
    
    # Инициализируем клиент Telegram
    logger.info("Инициализация клиента Telegram")
    client = get_client()
    await client.start()
    
    # Инициализируем базу данных
    logger.info("Инициализация базы данных")
    db = Database()
    
    try:
        # Собираем статистику для каждого канала
        channels = CHANNEL_IDS if CHANNEL_IDS else [CHANNEL_USERNAME]
        for channel in channels:
            await collect_channel_stats(client, db, channel)
            
    finally:
        logger.info("Отключение клиента Telegram")
        await client.disconnect()
        logger.info("Сбор статистики завершен")

if __name__ == "__main__":
    asyncio.run(main())
