from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from datetime import datetime
from .base import BaseCollector
from tgstats.database.models import ChannelParticipant
from tgstats.utils import convert_to_json_serializable
from sqlalchemy import and_

class ChannelParticipantsCollector(BaseCollector):
    async def run(self, channel):
        # Получаем информацию о канале
        chat = await self.client.get_entity(channel)
        
        # Получаем всех участников канала
        offset = 0
        limit = 200
        all_participants = []
        
        while True:
            participants = await self.client(GetParticipantsRequest(
                chat,
                ChannelParticipantsSearch(''),
                offset,
                limit,
                hash=0
            ))
            
            if not participants.users:
                break
                
            all_participants.extend(participants.users)
            offset += len(participants.users)
            
            if len(participants.users) < limit:
                break
        
        # Сохраняем информацию о каждом участнике
        for user in all_participants:
            # Проверяем, существует ли уже такой участник
            existing_participant = self.db.query(ChannelParticipant).filter(
                and_(
                    ChannelParticipant.channel_id == chat.id,
                    ChannelParticipant.user_id == user.id
                )
            ).first()
            
            if existing_participant:
                # Обновляем существующего участника
                existing_participant.username = user.username
                existing_participant.first_name = user.first_name
                existing_participant.last_name = user.last_name
                existing_participant.phone = user.phone
                existing_participant.raw = convert_to_json_serializable(user)
            else:
                # Добавляем нового участника
                participant = ChannelParticipant(
                    channel_id=chat.id,
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    phone=user.phone,
                    raw=convert_to_json_serializable(user)
                )
                self.db.add(participant)
        
        self.db.commit() 