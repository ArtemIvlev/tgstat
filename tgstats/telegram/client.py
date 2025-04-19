from telethon import TelegramClient as BaseTelegramClient
from telethon.tl.types import Channel, User, InputPeerChannel
from typing import Union

class TelegramClient(BaseTelegramClient):
    async def get_entity(self, peer: Union[int, str]) -> Union[Channel, User]:
        """
        Переопределяем метод get_entity для работы с каналами
        """
        # Преобразуем в число если это строка
        channel_id = int(peer) if isinstance(peer, str) else peer
        
        # Создаем InputPeerChannel с правильным ID и access_hash=0
        if channel_id > 0:
            return await super().get_entity(InputPeerChannel(channel_id, 0))
            
        return await super().get_entity(channel_id) 