from datetime import datetime, timedelta
from collections import defaultdict
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from .base import BaseCollector
from tgstats.database.models import DiscussionStats, ChannelPost
from tgstats.utils import convert_to_json_serializable
from sqlalchemy import and_

class DiscussionStatsCollector(BaseCollector):
    async def run(self, channel):
        chat = await self.client.get_entity(channel)
        
        # Получаем все посты за последние 7 дней
        week_ago = datetime.utcnow() - timedelta(days=7)
        posts = self.db.query(ChannelPost).filter(
            and_(
                ChannelPost.channel_id == chat.id,
                ChannelPost.date >= week_ago
            )
        ).all()
        
        # Собираем статистику обсуждений
        total_comments = 0
        active_users = set()
        comments_per_post = {}
        commenters = defaultdict(int)
        
        for post in posts:
            try:
                # Получаем обсуждение к посту
                discussion = await self.client(GetDiscussionMessageRequest(
                    peer=chat,
                    msg_id=post.message_id
                ))
                
                # Считаем комментарии
                comments_count = len(discussion.messages) - 1  # Исключаем сам пост
                total_comments += comments_count
                comments_per_post[str(post.message_id)] = comments_count
                
                # Собираем информацию о комментаторах
                for message in discussion.messages[1:]:  # Пропускаем сам пост
                    if hasattr(message, 'from_id') and message.from_id:
                        user_id = message.from_id.user_id
                        active_users.add(user_id)
                        commenters[user_id] += 1
            except Exception as e:
                print(f"Ошибка при получении обсуждения для поста {post.message_id}: {str(e)}")
        
        # Сортируем топ комментаторов
        top_commenters = sorted(
            [{"user_id": user_id, "comments": count} for user_id, count in commenters.items()],
            key=lambda x: x["comments"],
            reverse=True
        )[:10]  # Берем топ-10
        
        # Проверяем, есть ли уже запись за сегодня
        today = datetime.utcnow().date()
        existing_stats = self.db.query(DiscussionStats).filter(
            and_(
                DiscussionStats.channel_id == chat.id,
                DiscussionStats.date >= today
            )
        ).first()
        
        if existing_stats:
            # Обновляем существующую запись
            existing_stats.total_comments = total_comments
            existing_stats.active_users = len(active_users)
            existing_stats.comments_per_post = comments_per_post
            existing_stats.top_commenters = top_commenters
        else:
            # Создаем новую запись
            stats = DiscussionStats(
                channel_id=chat.id,
                total_comments=total_comments,
                active_users=len(active_users),
                comments_per_post=comments_per_post,
                top_commenters=top_commenters
            )
            self.db.add(stats)
        
        self.db.commit() 