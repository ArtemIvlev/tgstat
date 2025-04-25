from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from datetime import datetime, timedelta
from .base import BaseCollector
from tgstats.database.models import ChannelParticipant
from tgstats.utils import convert_to_json_serializable
from sqlalchemy import and_
from tgstats.logger import get_logger
from sqlalchemy.exc import SQLAlchemyError

logger = get_logger('collectors.channel_participants')

class ChannelParticipantsCollector(BaseCollector):
    async def run(self, channel):
        logger.info(f"Начало сбора участников канала: {channel}")
        
        try:
            # Получаем информацию о канале
            chat = await self.client.get_entity(channel)
            
            # Список букв, цифр и символов для поиска
            search_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                            'а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м',
                            'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ',
                            'ы', 'ь', 'э', 'ю', 'я',
                            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                            '_', '.', '-']
            
            all_participants = []
            current_time = datetime.utcnow()
            
            # Поиск участников по каждой букве
            for letter in search_letters:
                offset = 0
                limit = 200
                
                while True:
                    try:
                        participants = await self.client(GetParticipantsRequest(
                            channel=chat,
                            filter=ChannelParticipantsSearch(letter),
                            offset=offset,
                            limit=limit,
                            hash=0
                        ))
                        
                        if not participants.users:
                            break
                            
                        # Проверяем, нет ли уже этих пользователей в списке
                        new_users = [user for user in participants.users if user.id not in [p.id for p in all_participants]]
                        all_participants.extend(new_users)
                        total_count = len(all_participants)
                        logger.info(f"Получено {total_count} участников (поиск по '{letter}')")
                        
                        if len(participants.users) < limit:
                            break
                            
                        offset += limit
                    except Exception as e:
                        logger.error(f"Ошибка при получении участников по букве '{letter}': {str(e)}")
                        break
            
            logger.info(f"Всего получено {len(all_participants)} участников")
            
            # Сохраняем информацию о каждом участнике
            for user in all_participants:
                try:
                    # Начинаем новую транзакцию для каждого участника
                    self.db.session.begin_nested()
                    
                    # Проверяем, существует ли уже такой участник
                    existing_participant = self.db.query(ChannelParticipant).filter(
                        and_(
                            ChannelParticipant.channel_id == channel,
                            ChannelParticipant.user_id == user.id
                        )
                    ).first()
                    
                    if existing_participant:
                        # Обновляем существующего участника
                        existing_participant.username = user.username
                        existing_participant.first_name = user.first_name
                        existing_participant.last_name = user.last_name
                        existing_participant.phone = user.phone if hasattr(user, 'phone') else None
                        existing_participant.raw = convert_to_json_serializable(user)
                        existing_participant.updated_at = current_time
                        # Если участник был помечен как вышедший, сбрасываем это
                        if existing_participant.left_at:
                            existing_participant.left_at = None
                    else:
                        # Добавляем нового участника
                        participant = ChannelParticipant(
                            channel_id=channel,
                            user_id=user.id,
                            username=user.username,
                            first_name=user.first_name,
                            last_name=user.last_name,
                            phone=user.phone if hasattr(user, 'phone') else None,
                            raw=convert_to_json_serializable(user)
                        )
                        self.db.add(participant)
                    
                    # Фиксируем транзакцию для текущего участника
                    self.db.session.commit()
                    
                except Exception as e:
                    # Откатываем транзакцию в случае ошибки
                    self.db.session.rollback()
                    logger.error(f"Ошибка при обработке участника {user.id}: {str(e)}")
                    continue
            
            # Проверяем участников, которых нет в текущем списке
            ten_minutes_ago = current_time - timedelta(minutes=10)
            potentially_left_participants = self.db.query(ChannelParticipant).filter(
                and_(
                    ChannelParticipant.channel_id == channel,
                    ChannelParticipant.updated_at < ten_minutes_ago,
                    ChannelParticipant.left_at.is_(None)  # Проверяем только тех, кто еще не помечен как вышедший
                )
            ).all()
            
            if potentially_left_participants:
                logger.info(f"Проверка {len(potentially_left_participants)} потенциально вышедших участников")
                
                # Получаем список ID всех текущих участников
                current_participant_ids = {user.id for user in all_participants}
                
                # Проверяем каждого потенциально вышедшего участника
                for participant in potentially_left_participants:
                    if participant.user_id not in current_participant_ids:
                        try:
                            # Пробуем получить информацию о пользователе
                            try:
                                user = await self.client.get_entity(participant.user_id)
                                # Если получилось получить информацию, проверяем его права в канале
                                participant_info = await self.client.get_permissions(chat, user)
                                if not participant_info.is_member:
                                    # Если пользователь больше не участник, помечаем его как вышедшего
                                    participant.left_at = current_time
                                    self.db.session.commit()
                                    logger.info(f"Участник {participant.user_id} помечен как вышедший")
                            except Exception as e:
                                # Если не удалось получить информацию о пользователе,
                                # вероятно он действительно вышел из канала
                                participant.left_at = current_time
                                self.db.session.commit()
                                logger.info(f"Участник {participant.user_id} помечен как вышедший (не удалось получить информацию)")
                        except Exception as e:
                            self.db.session.rollback()
                            logger.error(f"Ошибка при проверке вышедшего участника {participant.user_id}: {str(e)}")
                            continue
            
            logger.info(f"Участники канала сохранены")
            
        except Exception as e:
            logger.error(f"Ошибка при сборе участников канала: {str(e)}")
            self.db.session.rollback()
            raise
        finally:
            # Закрываем сессию базы данных
            self.db.session.close() 