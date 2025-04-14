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

# Загружаем переменные окружения
load_dotenv()

# Получаем учетные данные из переменных окружения
API_ID = os.getenv('TG_API_ID')
API_HASH = os.getenv('TG_API_HASH')
CHANNEL_ID = os.getenv('TG_CHANNEL_ID')
CHANNEL_USERNAME = os.getenv('TG_CHANNEL_USERNAME')

async def main():
    # Инициализируем клиент Telegram
    client = TelegramClient('tgstats', API_ID, API_HASH)
    await client.start()
    
    # Инициализируем базу данных
    db = Database()
    
    try:
        # Определяем канал
        if CHANNEL_ID:
            channel = PeerChannel(int(CHANNEL_ID.replace('-100', '')))
        else:
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
                await collector.run(channel)
            except Exception as e:
                print(f"Ошибка в коллекторе {collector.__class__.__name__}: {str(e)}")
            
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
