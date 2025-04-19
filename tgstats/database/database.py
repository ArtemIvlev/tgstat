from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tgstats.database.models import Base, ChannelParticipant
from tgstats.config.config import PG_CONNECTION_PARAMS
from tgstats.database.schema import update_schema
from tgstats.logger import get_logger
from typing import List, Dict, Any, Optional
from sqlalchemy import text

logger = get_logger(__name__)

class Database:
    def __init__(self, config=None):
        # Формируем URL для подключения из параметров
        if config:
            self.config = config
            db_url = f"postgresql://{config.PG_CONNECTION_PARAMS['user']}:{config.PG_CONNECTION_PARAMS['password']}@{config.PG_CONNECTION_PARAMS['host']}:{config.PG_CONNECTION_PARAMS['port']}/{config.PG_CONNECTION_PARAMS['database']}"
        else:
            db_url = f"postgresql://{PG_CONNECTION_PARAMS['user']}:{PG_CONNECTION_PARAMS['password']}@{PG_CONNECTION_PARAMS['host']}:{PG_CONNECTION_PARAMS['port']}/{PG_CONNECTION_PARAMS['database']}"
        
        self.engine = create_engine(db_url)
        
        # Проверяем и обновляем схему базы данных
        if not update_schema(self.engine):
            logger.error("Не удалось обновить схему базы данных")
            raise Exception("Ошибка обновления схемы базы данных")
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def __enter__(self):
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def query(self, *args):
        return self.session.query(*args)
    
    def add(self, obj):
        self.session.add(obj)
    
    def commit(self):
        self.session.commit()
    
    def flush(self):
        self.session.flush()

    def get_channel_participants(self, channel_id: int) -> List[Dict[str, Any]]:
        """Получение списка участников канала"""
        try:
            logger.info(f"Запрос участников канала {channel_id}")
            # Устанавливаем таймаут в 30 секунд
            self.session.execute(text("SET statement_timeout = '30s'"))
            
            participants = self.session.query(ChannelParticipant).filter(
                ChannelParticipant.channel_id == channel_id
            ).all()
            
            logger.info(f"Найдено {len(participants)} участников")
            return [
                {
                    'user_id': p.user_id,
                    'first_name': p.first_name,
                    'last_name': p.last_name,
                    'username': p.username
                }
                for p in participants
            ]
        except Exception as e:
            logger.error(f"Ошибка при получении участников канала {channel_id}: {str(e)}")
            return []

    def get_participant(self, channel_id: int, user_id: int) -> Optional[ChannelParticipant]:
        """Получение участника канала по ID"""
        return self.session.query(ChannelParticipant).filter(
            ChannelParticipant.channel_id == channel_id,
            ChannelParticipant.user_id == user_id
        ).first() 