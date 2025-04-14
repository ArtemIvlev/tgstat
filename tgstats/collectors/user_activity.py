from datetime import datetime, timedelta
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterEmpty
from .base import BaseCollector
from tgstats.database.models import UserActivity, ChannelPost, ChannelParticipant
from tgstats.utils import convert_to_json_serializable
from sqlalchemy import and_, func

class UserActivityCollector(BaseCollector):
    async def run(self, channel):
        chat = await self.client.get_entity(channel)
        
        # Получаем всех участников из базы данных
        participants = self.db.query(ChannelParticipant).filter(
            ChannelParticipant.channel_id == chat.id
        ).all()
        
        # Анализируем активность за последние 30 дней
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        for participant in participants:
            try:
                # Получаем последнее сообщение пользователя через поиск
                search_result = await self.client(SearchRequest(
                    peer=chat,
                    q='',
                    filter=InputMessagesFilterEmpty(),
                    min_date=thirty_days_ago,
                    max_date=None,
                    offset_id=0,
                    add_offset=0,
                    limit=1,
                    max_id=0,
                    min_id=0,
                    from_id=participant.user_id,
                    hash=0
                ))
                
                messages = search_result.messages
                
                # Проверяем, есть ли уже запись активности за сегодня
                today = datetime.utcnow().date()
                existing_activity = self.db.query(UserActivity).filter(
                    and_(
                        UserActivity.channel_id == chat.id,
                        UserActivity.user_id == participant.user_id,
                        UserActivity.date >= today
                    )
                ).first()
                
                # Определяем статус активности
                is_active = bool(messages)
                last_message_date = messages[0].date if messages else None
                
                if existing_activity:
                    # Обновляем существующую запись
                    existing_activity.is_active = is_active
                    existing_activity.last_seen = last_message_date
                    existing_activity.last_post_date = last_message_date
                    existing_activity.raw = convert_to_json_serializable(participant.raw)
                else:
                    # Создаем новую запись
                    activity = UserActivity(
                        channel_id=chat.id,
                        user_id=participant.user_id,
                        is_active=is_active,
                        last_seen=last_message_date,
                        last_post_date=last_message_date,
                        raw=convert_to_json_serializable(participant.raw)
                    )
                    self.db.add(activity)
            except Exception as e:
                print(f"Ошибка при обработке участника {participant.user_id}: {str(e)}")
        
        self.db.commit() 