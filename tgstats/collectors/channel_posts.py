from datetime import datetime, timedelta
from telethon.tl.functions.messages import GetHistoryRequest
from .base import BaseCollector
from tgstats.database.models import ChannelPost, PostReaction
from tgstats.utils import convert_to_json_serializable
from sqlalchemy import and_
from tgstats.logger import get_logger

logger = get_logger('collectors.channel_posts')

class ChannelPostsCollector(BaseCollector):
    async def run(self, channel):
        logger.info(f"Начало сбора постов канала: {channel}")
        
        # Получаем все сообщения канала
        chat = await self.client.get_entity(channel)
        posts = await self.client.get_messages(chat, limit=None)
        
        # Собираем статистику
        now = datetime.utcnow().replace(tzinfo=None)  # Убираем информацию о часовом поясе
        week_ago = now - timedelta(days=7)
        
        # Словарь для хранения ID постов в базе данных
        post_ids = {}
        
        # Обрабатываем каждый пост
        for message in posts:
            if not message.date:
                continue
                
            # Убираем информацию о часовом поясе для сравнения
            message_date = message.date.replace(tzinfo=None)
            
            # Считаем только посты за последнюю неделю
            if message_date < week_ago:
                continue
                
            # Проверяем, есть ли уже такой пост в базе
            existing_post = self.db.query(ChannelPost).filter(
                and_(
                    ChannelPost.channel_id == chat.id,
                    ChannelPost.message_id == message.id
                )
            ).first()
            
            if existing_post:
                # Обновляем существующий пост
                existing_post.views = message.views
                existing_post.forwards = message.forwards
                existing_post.text = message.text
                existing_post.date = message_date
                existing_post.media_type = message.media.__class__.__name__ if message.media else None
                existing_post.replies = message.replies.replies if message.replies else 0
                existing_post.raw = convert_to_json_serializable(message)
                post_ids[message.id] = existing_post.id
            else:
                # Создаем новый пост
                post = ChannelPost(
                    channel_id=chat.id,
                    message_id=message.id,
                    views=message.views,
                    forwards=message.forwards,
                    text=message.text,
                    date=message_date,
                    media_type=message.media.__class__.__name__ if message.media else None,
                    replies=message.replies.replies if message.replies else 0,
                    raw=convert_to_json_serializable(message)
                )
                self.db.add(post)
                self.db.flush()  # Получаем ID нового поста
                post_ids[message.id] = post.id
        
        self.db.commit()
        logger.info(f"Посты канала за последнюю неделю сохранены")

        # Сохраняем реакции
        for message in posts:
            if message.reactions and message.reactions.results:
                # Пропускаем реакции для постов, которых нет в базе
                if message.id not in post_ids:
                    continue
                    
                for reaction_count in message.reactions.results:
                    if reaction_count.reaction:
                        # Получаем тип реакции
                        reaction_data = convert_to_json_serializable(reaction_count.reaction)
                        reaction_type = reaction_data.get('emoticon') if isinstance(reaction_data, dict) else str(reaction_data)
                        
                        # Проверяем, существует ли уже реакция
                        existing_reaction = self.db.query(PostReaction).filter(
                            and_(
                                PostReaction.post_id == post_ids[message.id],
                                PostReaction.reaction == reaction_type
                            )
                        ).first()
                        
                        if existing_reaction:
                            # Обновляем количество реакций
                            existing_reaction.count = reaction_count.count
                        else:
                            # Создаем новую реакцию
                            new_reaction = PostReaction(
                                post_id=post_ids[message.id],
                                reaction=reaction_type,
                                count=reaction_count.count,
                                date=message.date.replace(tzinfo=None)  # Убираем информацию о часовом поясе
                            )
                            self.db.add(new_reaction)
        
        self.db.commit() 