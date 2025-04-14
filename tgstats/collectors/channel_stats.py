from telethon.tl.functions.channels import GetFullChannelRequest
from datetime import datetime
from .base import BaseCollector
from tgstats.database.models import ChannelStats
from tgstats.config import CHANNEL_TITLE
from sqlalchemy import and_

def convert_to_json_serializable(obj):
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    return obj

class ChannelStatsCollector(BaseCollector):
    async def run(self, channel):
        # Получаем информацию о канале
        chat = await self.client.get_entity(channel)
        full_chat = await self.client(GetFullChannelRequest(chat))

        # Преобразуем данные для JSON
        raw_data = convert_to_json_serializable(full_chat.full_chat.to_dict())

        # Проверяем, есть ли уже запись за сегодня
        today = datetime.utcnow().date()
        existing_stats = self.db.query(ChannelStats).filter(
            and_(
                ChannelStats.channel_id == chat.id,
                ChannelStats.date >= today
            )
        ).first()
        
        if existing_stats:
            # Обновляем существующую статистику за сегодня
            existing_stats.title = CHANNEL_TITLE
            existing_stats.username = chat.username
            existing_stats.subscribers = full_chat.full_chat.participants_count
            existing_stats.raw = raw_data
        else:
            # Создаем новую запись статистики
            stats = ChannelStats(
                channel_id=chat.id,
                title=CHANNEL_TITLE,
                username=chat.username,
                subscribers=full_chat.full_chat.participants_count,
                raw=raw_data
            )
            self.db.add(stats)
        
        self.db.commit()
