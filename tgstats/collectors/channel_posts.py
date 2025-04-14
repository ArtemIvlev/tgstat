from telethon.tl.functions.messages import GetHistoryRequest
from .base import BaseCollector
from tgstats.database.models import ChannelPost, PostReaction
from tgstats.utils import convert_to_json_serializable
from sqlalchemy import and_

class ChannelPostsCollector(BaseCollector):
    async def run(self, channel):
        chat = await self.client.get_entity(channel)
        
        # Получаем все сообщения из канала
        messages = []
        offset_id = 0
        limit = 100
        total_messages = 0
        total_limit = 1000  # Ограничиваем количество сообщений
        
        while True:
            history = await self.client(GetHistoryRequest(
                peer=chat,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            
            if not history.messages:
                break
                
            messages.extend(history.messages)
            total_messages += len(history.messages)
            
            if total_messages >= total_limit:
                break
                
            offset_id = messages[-1].id
        
        # Сохраняем сообщения и реакции
        for message in messages:
            # Проверяем, существует ли уже пост
            existing_post = self.db.query(ChannelPost).filter(
                and_(
                    ChannelPost.channel_id == chat.id,
                    ChannelPost.message_id == message.id
                )
            ).first()
            
            if existing_post:
                # Обновляем существующий пост
                existing_post.text = message.text
                existing_post.views = message.views
                existing_post.forwards = message.forwards
                existing_post.replies = message.replies.replies if message.replies else None
                existing_post.raw = convert_to_json_serializable(message)
            else:
                # Создаем новый пост
                post = ChannelPost(
                    channel_id=chat.id,
                    message_id=message.id,
                    date=message.date,
                    text=message.text,
                    views=message.views,
                    forwards=message.forwards,
                    replies=message.replies.replies if message.replies else None,
                    media_type=message.media.__class__.__name__ if message.media else None,
                    raw=convert_to_json_serializable(message)
                )
                self.db.add(post)
                self.db.flush()  # Получаем ID поста для реакций
            
            # Обрабатываем реакции
            if message.reactions and message.reactions.results:
                for reaction_count in message.reactions.results:
                    if reaction_count.reaction:
                        # Получаем тип реакции
                        reaction_data = convert_to_json_serializable(reaction_count.reaction)
                        reaction_type = reaction_data.get('emoticon') if isinstance(reaction_data, dict) else str(reaction_data)
                        
                        # Проверяем, существует ли уже реакция
                        existing_reaction = self.db.query(PostReaction).filter(
                            and_(
                                PostReaction.post_id == (existing_post.id if existing_post else post.id),
                                PostReaction.reaction == reaction_type
                            )
                        ).first()
                        
                        if existing_reaction:
                            # Обновляем количество реакций
                            existing_reaction.count = reaction_count.count
                        else:
                            # Создаем новую реакцию
                            new_reaction = PostReaction(
                                post_id=existing_post.id if existing_post else post.id,
                                reaction=reaction_type,
                                count=reaction_count.count,
                                date=message.date
                            )
                            self.db.add(new_reaction)
        
        self.db.commit() 