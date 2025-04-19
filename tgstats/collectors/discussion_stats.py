from datetime import datetime, timedelta
from collections import defaultdict
from .base import BaseCollector
from tgstats.database.models import DiscussionStats, ChannelPost
from tgstats.utils import convert_to_json_serializable
from sqlalchemy import and_
from tgstats.logger import get_logger

logger = get_logger(__name__)

class DiscussionStatsCollector(BaseCollector):
    def __init__(self, client, db):
        super().__init__(client, db)
        self.today = datetime.utcnow().date()
    
    async def run(self, channel):
        """Сбор статистики обсуждений канала"""
        logger.info(f"Начало сбора статистики обсуждений канала: {channel}")
        
        try:
            chat = await self.client.get_entity(channel)
        except ValueError as e:
            logger.error(f"Ошибка при получении информации о канале: {str(e)}")
            return
        
        # Получаем все посты из базы
        posts = self.db.query(ChannelPost).filter(
            ChannelPost.channel_id == chat.id
        ).all()
        
        logger.info(f"Найдено {len(posts)} постов в базе")
        
        # Собираем статистику обсуждений
        total_comments = 0
        active_users = set()
        comments_per_post = {}
        commenters = defaultdict(int)
        
        for post in posts:
            try:
                # Получаем комментарии к посту через get_messages
                replies = await self.client.get_messages(
                    chat,
                    reply_to=post.message_id,
                    limit=100  # Увеличиваем лимит для получения большего количества комментариев
                )
                
                if not replies:
                    logger.debug(f"Пост {post.message_id} не имеет комментариев")
                    continue
                
                # Считаем комментарии
                comments_count = len(replies)
                total_comments += comments_count
                comments_per_post[str(post.message_id)] = comments_count
                
                logger.debug(f"Пост {post.message_id}: {comments_count} комментариев")
                
                # Собираем информацию о комментаторах
                for reply in replies:
                    if hasattr(reply, 'from_id') and reply.from_id:
                        user_id = reply.from_id.user_id
                        active_users.add(user_id)
                        commenters[user_id] += 1
            except Exception as e:
                logger.warning(f"Ошибка при получении комментариев для поста {post.message_id}: {str(e)}")
                continue
        
        # Сортируем топ комментаторов
        top_commenters = sorted(
            [{"user_id": user_id, "comments": count} for user_id, count in commenters.items()],
            key=lambda x: x["comments"],
            reverse=True
        )[:10]  # Берем топ-10
        
        # Проверяем, есть ли уже запись за сегодня
        existing_stats = self.db.query(DiscussionStats).filter(
            and_(
                DiscussionStats.channel_id == chat.id,
                DiscussionStats.date >= self.today
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
        logger.info(f"Статистика обсуждений сохранена: {total_comments} комментариев, {len(active_users)} активных пользователей")
        
        # Выводим детальную информацию о комментариях
        if total_comments > 0:
            logger.info("\nДетальная информация о комментариях:")
            for post_id, comments in comments_per_post.items():
                logger.info(f"Пост {post_id}: {comments} комментариев")
            
            if top_commenters:
                logger.info("\nТоп комментаторов:")
                for i, commenter in enumerate(top_commenters, 1):
                    logger.info(f"{i}. Пользователь {commenter['user_id']}: {commenter['comments']} комментариев") 