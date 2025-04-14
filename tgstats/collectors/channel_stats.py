from telethon.tl.functions.channels import GetFullChannelRequest
from datetime import datetime
from .base import BaseCollector
from tgstats.database.models import ChannelStats
from tgstats.config.config import CHANNEL_TITLE
from sqlalchemy import and_
from tgstats.logger import get_logger

# Создаем логгер для этого модуля
logger = get_logger('collectors.channel_stats')

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
        logger.info(f"Начало сбора статистики канала: {channel}")
        
        # Получаем информацию о канале
        logger.info("Получение информации о канале")
        chat = await self.client.get_entity(channel)
        logger.info(f"Получена информация о канале: {chat.title} (ID: {chat.id})")
        
        logger.info("Получение полной информации о канале")
        full_chat = await self.client(GetFullChannelRequest(chat))
        logger.info(f"Получена полная информация о канале. Подписчиков: {full_chat.full_chat.participants_count}")

        # Преобразуем данные для JSON
        logger.info("Преобразование данных для сохранения")
        raw_data = convert_to_json_serializable(full_chat.full_chat.to_dict())

        # Проверяем, есть ли уже запись за сегодня
        today = datetime.utcnow().date()
        logger.info(f"Проверка существующих записей за {today}")
        existing_stats = self.db.query(ChannelStats).filter(
            and_(
                ChannelStats.channel_id == chat.id,
                ChannelStats.date >= today
            )
        ).first()
        
        if existing_stats:
            # Обновляем существующую статистику за сегодня
            logger.info("Обновление существующей записи статистики")
            existing_stats.title = CHANNEL_TITLE
            existing_stats.username = chat.username
            existing_stats.subscribers = full_chat.full_chat.participants_count
            existing_stats.raw = raw_data
        else:
            # Создаем новую запись статистики
            logger.info("Создание новой записи статистики")
            stats = ChannelStats(
                channel_id=chat.id,
                title=CHANNEL_TITLE,
                username=chat.username,
                subscribers=full_chat.full_chat.participants_count,
                raw=raw_data
            )
            self.db.add(stats)
        
        logger.info("Сохранение изменений в базе данных")
        self.db.commit()
        logger.info("Статистика канала успешно сохранена")
