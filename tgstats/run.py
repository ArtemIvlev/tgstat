import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from tgstats.database import Database
from tgstats.collectors.channel_stats import ChannelStatsCollector
from tgstats.collectors.channel_posts import ChannelPostsCollector
from tgstats.collectors.channel_participants import ChannelParticipantsCollector
from tgstats.collectors.user_activity import UserActivityCollector

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
    
    # Определяем идентификатор канала
    channel_identifier = CHANNEL_ID or CHANNEL_USERNAME
    
    if channel_identifier.replace('-', '').isdigit():
        channel_id = channel_identifier.replace('-100', '')
        channel = PeerChannel(int(channel_id))
    else:
        channel = channel_identifier
    
    # Создаем коллекторы
    collectors = [
        ChannelStatsCollector(client, db),
        ChannelPostsCollector(client, db),
        ChannelParticipantsCollector(client, db),
        UserActivityCollector(client, db)
    ]
    
    # Запускаем все коллекторы
    for collector in collectors:
        try:
            await collector.run(channel)
        except Exception as e:
            print(f"Ошибка в коллекторе {collector.__class__.__name__}: {str(e)}")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
