import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from tgstats.database import Database
from tgstats.collectors.channel_stats import ChannelStatsCollector
from tgstats.collectors.channel_posts import ChannelPostsCollector
from tgstats.collectors.channel_participants import ChannelParticipantsCollector
from tgstats.collectors.channel_activity import ChannelActivityCollector
from tgstats.collectors.discussion_stats import DiscussionStatsCollector
from tgstats.logger import get_logger

# Загружаем переменные окружения
load_dotenv()

# Получаем учетные данные из переменных окружения
API_ID = os.getenv('TG_API_ID')
API_HASH = os.getenv('TG_API_HASH')
CHANNEL_ID = os.getenv('TG_CHANNEL_ID')
CHANNEL_USERNAME = os.getenv('TG_CHANNEL_USERNAME')

# Создаем логгер
logger = get_logger('run')

async def main():
    logger.info("Запуск сбора статистики канала")
    
    # Инициализируем клиент Telegram
    logger.info("Инициализация клиента Telegram")
    client = TelegramClient('tgstats', API_ID, API_HASH)
    await client.start()
    
    # Инициализируем базу данных
    logger.info("Инициализация базы данных")
    db = Database()
    
    try:
        # Определяем канал
        if CHANNEL_ID:
            logger.info(f"Используется ID канала: {CHANNEL_ID}")
            channel = PeerChannel(int(CHANNEL_ID.replace('-100', '')))
        else:
            logger.info(f"Используется юзернейм канала: {CHANNEL_USERNAME}")
            channel = CHANNEL_USERNAME
        
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
                logger.info(f"Запуск коллектора: {collector.__class__.__name__}")
                await collector.run(channel)
                logger.info(f"Коллектор {collector.__class__.__name__} успешно завершил работу")
            except Exception as e:
                logger.error(f"Ошибка в коллекторе {collector.__class__.__name__}: {str(e)}", exc_info=True)
            
    finally:
        logger.info("Отключение клиента Telegram")
        await client.disconnect()
        logger.info("Сбор статистики завершен")

if __name__ == '__main__':
    asyncio.run(main())
