from datetime import datetime
from .base import BaseCollector
from tgstats.database.models import PostComment, CommentReaction, ChannelPost
from tgstats.utils import convert_to_json_serializable
from sqlalchemy import and_
from tgstats.logger import get_logger
from telethon.tl.types import PeerUser, PeerChannel, PeerChat, ReactionEmoji
from telethon.tl.functions.messages import GetDiscussionMessageRequest

logger = get_logger(__name__)

def get_peer_id(peer):
    """Извлекает ID из разных типов пиров"""
    if isinstance(peer, (int, str)):
        return int(peer)
    elif hasattr(peer, 'user_id'):
        return peer.user_id
    elif hasattr(peer, 'channel_id'):
        return peer.channel_id
    elif hasattr(peer, 'chat_id'):
        return peer.chat_id
    return None

class PostCommentsCollector(BaseCollector):
    async def run(self, channel):
        """Сбор комментариев к постам канала"""
        logger.info(f"Начало сбора комментариев канала: {channel}")
        
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
        
        for post in posts:
            try:
                # Получаем комментарии к посту
                comments = await self.client.get_messages(
                    chat,
                    reply_to=post.message_id,
                    limit=100
                )
                
                if not comments:
                    logger.debug(f"Пост {post.message_id} не имеет комментариев")
                    continue
                
                logger.info(f"Найдено {len(comments)} комментариев для поста {post.message_id}")
                
                # Обрабатываем каждый комментарий
                for comment in comments:
                    try:
                        # Пропускаем комментарии без автора
                        if not comment.from_id:
                            logger.debug(f"Пропуск комментария {comment.id} без автора")
                            continue
                            
                        # Проверяем, существует ли уже такой комментарий
                        existing_comment = self.db.query(PostComment).filter(
                            and_(
                                PostComment.channel_id == chat.id,
                                PostComment.message_id == comment.id
                            )
                        ).first()
                        
                        comment_data = {
                            'channel_id': chat.id,
                            'post_id': post.id,
                            'message_id': comment.id,
                            'user_id': get_peer_id(comment.from_id),
                            'text': comment.text,
                            'date': comment.date.replace(tzinfo=None),
                            'views': comment.views or 0,
                            'forwards': comment.forwards or 0,
                            'likes': 0,  # Будет обновлено из реакций
                            'raw': convert_to_json_serializable(comment)
                        }
                        
                        if existing_comment:
                            # Обновляем существующий комментарий
                            for key, value in comment_data.items():
                                setattr(existing_comment, key, value)
                            
                            # Удаляем старые реакции
                            self.db.query(CommentReaction).filter(
                                CommentReaction.comment_id == comment.id
                            ).delete()
                        else:
                            # Создаем новый комментарий
                            new_comment = PostComment(**comment_data)
                            self.db.add(new_comment)
                            
                        try:
                            # Сохраняем комментарий
                            self.db.commit()
                            
                            # Получаем ID сохраненного комментария
                            comment_id = existing_comment.id if existing_comment else new_comment.id
                            
                            # Сохраняем реакции только после успешного сохранения комментария
                            if hasattr(comment, 'reactions') and comment.reactions:
                                logger.info(f"Найдены реакции для комментария {comment.id}: {convert_to_json_serializable(comment.reactions)}")
                                
                                # Обрабатываем реакции из recent_reactions
                                if hasattr(comment.reactions, 'recent_reactions'):
                                    logger.info(f"Тип comment.id: {type(comment.id)}, значение: {comment.id}")
                                    logger.info(f"Структура комментария: {convert_to_json_serializable(comment)}")
                                    for reaction in comment.reactions.recent_reactions:
                                        user_id = get_peer_id(reaction.peer_id)
                                        if user_id:
                                            reaction_data = {
                                                'comment_id': comment_id,  # Используем ID из базы данных
                                                'user_id': user_id,
                                                'reaction': str(reaction.reaction.emoticon),
                                                'date': reaction.date.strftime('%Y-%m-%d %H:%M:%S')
                                            }
                                            db_reaction = CommentReaction(**reaction_data)
                                            self.db.add(db_reaction)
                                            logger.info(f"Сохранена реакция {reaction_data['reaction']} от пользователя {user_id}")
                                            
                                            # Если это лайк, обновляем счетчик лайков
                                            if reaction_data['reaction'] == '👍':
                                                comment_data['likes'] += 1
                                    
                                    # Сохраняем реакции
                                    self.db.commit()
                                    
                        except Exception as e:
                            logger.error(f"Ошибка при сохранении комментария {comment.id}: {str(e)}")
                            self.db.rollback()
                            continue
                        
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке комментария {comment.id}: {str(e)}")
                        try:
                            self.db.rollback()
                        except:
                            pass
                        continue
                
            except Exception as e:
                logger.warning(f"Ошибка при получении комментариев для поста {post.message_id}: {str(e)}")
                continue
        
        logger.info("Комментарии успешно сохранены")

    async def collect_comments(self):
        """Collect comments for all posts in the channel."""
        self.logger.info(f"Collecting comments for channel {self.channel_username}")
        
        channel = await self.get_channel()
        if not channel:
            return
        
        posts = await self.get_posts()
        if not posts:
            return
        
        for post in posts:
            try:
                comments = await self.client.get_messages(
                    channel,
                    reply_to=post['message_id']
                )
                
                logger.info(f"Processing {len(comments)} comments for post {post['message_id']}")
                
                for comment in comments:
                    try:
                        # Skip if comment already exists
                        existing = self.db.query(PostComment).filter(
                            PostComment.message_id == comment.id
                        ).first()
                        
                        if existing:
                            continue
                            
                        # Get comment reactions
                        reactions_list = await self.client(GetDiscussionMessageRequest(
                            peer=f"@{channel.username}_discussion",
                            msg_id=comment.id
                        ))
                        
                        # Prepare comment data
                        comment_data = {
                            'channel_id': channel.id,
                            'post_id': post['message_id'],
                            'message_id': comment.id,
                            'user_id': get_peer_id(comment.from_id),
                            'text': comment.message,
                            'date': comment.date,
                            'views': getattr(comment, 'views', 0),
                            'forwards': getattr(comment, 'forwards', 0),
                            'likes': len(reactions_list.reactions) if reactions_list else 0,
                            'raw': str(comment.to_dict())
                        }
                        
                        # Save comment
                        db_comment = PostComment(**comment_data)
                        self.db.add(db_comment)
                        
                        # Save reactions
                        if reactions_list and reactions_list.reactions:
                            for reaction in reactions_list.reactions:
                                user_id = get_peer_id(reaction.peer_id)
                                if user_id:
                                    reaction_data = {
                                        'comment_id': comment.id,
                                        'user_id': user_id,
                                        'reaction': str(reaction.reaction.emoticon),
                                        'date': reaction.date.strftime('%Y-%m-%d %H:%M:%S')
                                    }
                                    db_reaction = CommentReaction(**reaction_data)
                                    self.db.add(db_reaction)
                        
                        self.db.commit()
                        
                    except Exception as e:
                        logger.error(f"Error processing comment {comment.id}: {str(e)}")
                        self.db.rollback()
                        
            except Exception as e:
                logger.error(f"Error collecting comments for post {post['message_id']}: {e}")
                continue
            
        self.logger.info(f"Finished collecting comments for channel {self.channel_username}")

    async def process_comment(self, comment, post, db):
        try:
            comment_data = {
                'message_id': comment.id,
                'channel_id': post.channel_id,
                'post_id': post.message_id,
                'user_id': get_peer_id(comment.from_id) if comment.from_id else None,
                'text': comment.message,
                'date': comment.date,
                'reply_to': comment.reply_to.reply_to_msg_id if comment.reply_to else None
            }

            # Создаем и сохраняем комментарий
            db_comment = PostComment(**comment_data)
            db.session.add(db_comment)
            db.session.commit()  # Сохраняем комментарий перед обработкой реакций

            # Обрабатываем реакции после сохранения комментария
            if hasattr(comment, 'reactions') and comment.reactions:
                logger.info(f"Найдены реакции для комментария {comment.id}: {comment.reactions}")
                logger.info(f"Тип comment.id: {type(comment.id)}, значение: {comment.id}")
                logger.info(f"Структура комментария: {comment}")

                if hasattr(comment.reactions, 'recent_reactions'):
                    for reaction in comment.reactions.recent_reactions:
                        user_id = get_peer_id(reaction.peer_id)
                        if user_id:
                            reaction_data = {
                                'comment_id': comment.id,
                                'user_id': user_id,
                                'reaction': reaction.reaction.emoticon,
                                'date': reaction.date
                            }
                            try:
                                db_reaction = CommentReaction(**reaction_data)
                                db.session.add(db_reaction)
                                db.session.commit()
                                logger.info(f"Сохранена реакция {reaction.reaction.emoticon} от пользователя {user_id}")
                            except Exception as e:
                                logger.error(f"Ошибка при сохранении реакции: {str(e)}")
                                db.session.rollback()

        except Exception as e:
            logger.error(f"Ошибка при сохранении комментария {comment.id}: {str(e)}")
            db.session.rollback()
            raise 