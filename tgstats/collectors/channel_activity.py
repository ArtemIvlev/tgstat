from datetime import datetime, timedelta
from telethon.tl.functions.messages import GetHistoryRequest
from .base import BaseCollector
from tgstats.database.models import HourlyActivity
from tgstats.logger import get_logger

logger = get_logger(__name__)

class ChannelActivityCollector(BaseCollector):
    """Сборщик статистики активности канала"""
    
    def __init__(self, client, db):
        super().__init__(client, db)
        self.today = datetime.now().date()
        self.yesterday = self.today - timedelta(days=1)
    
    async def run(self, channel):
        """Сбор статистики активности канала"""
        self.channel = await self.client.get_entity(channel)
        logger.info(f"Начинаю сбор статистики активности для канала {self.channel.title}")
        
        # Инициализация счетчиков
        active_hours = {hour: {
            'views': 0,
            'forwards': 0,
            'reactions': 0,
            'posts_count': 0
        } for hour in range(24)}
        
        # Получаем все сообщения за последние 24 часа
        messages = await self.client.get_messages(
            self.channel,
            limit=None,
            offset_date=None,
            reverse=True
        )
        
        for message in messages:
            message_date = message.date.date()
            
            # Пропускаем сообщения старше вчерашнего дня
            if message_date < self.yesterday:
                continue
                
            # Получаем час публикации
            hour = message.date.hour
            
            # Обновляем статистику
            active_hours[hour]['views'] += message.views or 0
            active_hours[hour]['forwards'] += message.forwards or 0
            
            # Проверяем наличие реакций
            if hasattr(message, 'reactions') and message.reactions:
                active_hours[hour]['reactions'] += sum(
                    reaction.count for reaction in message.reactions.results
                )
            
            active_hours[hour]['posts_count'] += 1
        
        # Сохраняем статистику в базу данных
        for hour, stats in active_hours.items():
            # Проверяем существующую запись
            existing = self.db.query(HourlyActivity).filter(
                HourlyActivity.channel_id == self.channel.id,
                HourlyActivity.date == self.today,
                HourlyActivity.hour == hour
            ).first()
            
            if existing:
                # Обновляем существующую запись
                existing.views = stats['views']
                existing.forwards = stats['forwards']
                existing.reactions = stats['reactions']
                existing.posts_count = stats['posts_count']
                existing.updated_at = datetime.utcnow()
            else:
                # Создаем новую запись
                activity = HourlyActivity(
                    channel_id=self.channel.id,
                    date=self.today,
                    hour=hour,
                    views=stats['views'],
                    forwards=stats['forwards'],
                    reactions=stats['reactions'],
                    posts_count=stats['posts_count']
                )
                self.db.add(activity)
        
        self.db.commit()
        logger.info(f"Статистика активности для канала {self.channel.title} успешно сохранена")
        
        # Логируем распределение просмотров по часам
        for hour, stats in active_hours.items():
            logger.info(f"Час {hour:02d}:00 - {stats['views']} просмотров, {stats['forwards']} репостов, {stats['reactions']} реакций, {stats['posts_count']} постов") 