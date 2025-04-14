from datetime import datetime, timedelta
from collections import defaultdict
from .base import BaseCollector
from tgstats.database.models import ChannelActivity, ChannelPost, PostReaction
from tgstats.utils import convert_to_json_serializable
from sqlalchemy import and_, func

class ChannelActivityCollector(BaseCollector):
    async def run(self, channel):
        chat = await self.client.get_entity(channel)
        
        # Получаем все посты за последние 24 часа
        yesterday = datetime.utcnow() - timedelta(days=1)
        posts = self.db.query(ChannelPost).filter(
            and_(
                ChannelPost.channel_id == chat.id,
                ChannelPost.date >= yesterday
            )
        ).all()
        
        # Собираем статистику
        total_views = sum(post.views for post in posts)
        total_forwards = sum(post.forwards for post in posts)
        total_reactions = self.db.query(func.sum(PostReaction.count)).filter(
            PostReaction.post_id.in_([post.id for post in posts])
        ).scalar() or 0
        
        # Анализируем активность по часам
        active_hours = defaultdict(int)
        for post in posts:
            hour = post.date.hour
            active_hours[str(hour)] += post.views
        
        # Проверяем, есть ли уже запись за сегодня
        today = datetime.utcnow().date()
        existing_activity = self.db.query(ChannelActivity).filter(
            and_(
                ChannelActivity.channel_id == chat.id,
                ChannelActivity.date >= today
            )
        ).first()
        
        if existing_activity:
            # Обновляем существующую запись
            existing_activity.total_views = total_views
            existing_activity.total_forwards = total_forwards
            existing_activity.total_reactions = total_reactions
            existing_activity.posts_count = len(posts)
            existing_activity.active_hours = active_hours
        else:
            # Создаем новую запись
            activity = ChannelActivity(
                channel_id=chat.id,
                total_views=total_views,
                total_forwards=total_forwards,
                total_reactions=total_reactions,
                posts_count=len(posts),
                active_hours=active_hours
            )
            self.db.add(activity)
        
        self.db.commit() 