import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from transliterate import translit
from tqdm import tqdm
import pandas as pd

from tgstats.database.database import Database
from tgstats.config.config import Config
from tgstats.database.models import ChannelParticipant

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/gender_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

class GenderAnalyzer:
    def __init__(self, db: Database):
        self.db = db
        self.device = 0 if torch.cuda.is_available() else -1
        logger.info(f"Используется устройство: {'CUDA' if self.device == 0 else 'CPU'}")
        
        # Инициализация модели
        logger.info("Загрузка модели для определения пола...")
        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        self.model = AutoModelForSequenceClassification.from_pretrained("Tillicollaps/Gender-Classification-russian-name")
        self.classifier = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            device=self.device
        )
        logger.info("Модель загружена успешно")

    def transliterate_name(self, text: str) -> str:
        """Транслитерация русского текста в латиницу"""
        try:
            return translit(text, language_code='ru', reversed=True)
        except Exception:
            return text

    def infer_gender(self, row: Dict[str, Any]) -> tuple:
        """Определение пола по имени, фамилии и username"""
        parts = [row['first_name'], row['last_name'], row['username']]
        text = " ".join(p for p in parts if p)
        text = self.transliterate_name(text)
        try:
            result = self.classifier(text, truncation=True, max_length=128)[0]
            return result['label'], result['score']
        except Exception:
            return "unknown", 0.0

    def analyze_participants(self, channel_ids: List[int]) -> None:
        """Анализ пола участников для указанных каналов"""
        for channel_id in channel_ids:
            logger.info(f"Анализ пола участников для канала {channel_id}")
            
            # Получение участников из базы данных
            participants = self.db.get_channel_participants(channel_id)
            logger.info(f"Всего участников в базе: {len(participants)}")
            
            if not participants:
                logger.warning(f"Нет данных об участниках для канала {channel_id}")
                continue

            # Фильтрация участников, у которых еще не определен пол
            participants_to_analyze = [
                p for p in participants 
                if not p.get('gender') or p.get('gender') == 'unknown'
            ]
            
            logger.info(f"Участников для анализа: {len(participants_to_analyze)}")
            if not participants_to_analyze:
                logger.info(f"Все участники канала {channel_id} уже проанализированы")
                continue

            # Определение пола
            logger.info("Начинаем определение пола участников...")
            results = []
            for participant in tqdm(participants_to_analyze, desc="Анализ участников", unit="участник"):
                gender, confidence = self.infer_gender(participant)
                results.append({
                    'user_id': participant['user_id'],
                    'first_name': participant['first_name'],
                    'last_name': participant['last_name'],
                    'username': participant['username'],
                    'gender': gender,
                    'confidence': confidence
                })
                logger.debug(f"Проанализирован участник {participant['user_id']}: {gender} ({confidence:.2f})")

            # Преобразование в DataFrame
            df = pd.DataFrame(results)
            
            # Сохранение результатов в базу данных
            logger.info("Сохранение результатов в базу данных...")
            for _, row in df.iterrows():
                participant = self.db.get_participant(channel_id, row['user_id'])
                if participant:
                    participant.gender = row['gender'].lower()
                    participant.gender_confidence = row['confidence']
                    participant.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info("Результаты сохранены в базу данных")

            # Вывод статистики
            df['gender'] = df['gender'].str.lower()
            counts = df['gender'].value_counts(normalize=True).round(4) * 100
            logger.info(f"\nГендерное распределение для новых участников канала {channel_id}:")
            for gender in ['male', 'female', 'unknown']:
                percent = counts.get(gender, 0.0)
                logger.info(f"  {gender:>7}: {percent:.2f}%")

async def main():
    # Создание необходимых директорий
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)

    # Инициализация конфигурации и базы данных
    config = Config()
    db = Database(config)

    # Создание анализатора
    analyzer = GenderAnalyzer(db)

    try:
        # Анализ пола для всех каналов
        analyzer.analyze_participants(config.CHANNEL_IDS)
    finally:
        # Закрытие соединения с базой данных
        db.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 