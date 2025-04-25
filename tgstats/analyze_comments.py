from dotenv import load_dotenv
from tgstats.database import Database
from tgstats.analytics.comment_analytics import CommentAnalytics
from tgstats.config.config import CHANNEL_IDS, CHANNEL_USERNAME
from tgstats.logger import get_logger
import json
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

# Создаем логгер
logger = get_logger(__name__)

def format_stats(stats):
    """Форматирует статистику для вывода"""
    return json.dumps(stats, indent=2, ensure_ascii=False, default=str)

def analyze_channel_comments(channel_id):
    """Анализирует комментарии для указанного канала"""
    logger.info(f"Анализ комментариев для канала {channel_id}")
    
    # Инициализируем базу данных
    db = Database()
    
    # Создаем анализатор
    analyzer = CommentAnalytics(db)
    
    # Получаем общую статистику
    stats = analyzer.get_channel_stats(channel_id)
    logger.info("Общая статистика:")
    logger.info(json.dumps(format_stats(stats), indent=2, ensure_ascii=False))
    
    # Получаем топ комментаторов
    top_commenters = analyzer.get_top_commenters(channel_id)
    logger.info("\nТоп комментаторов:")
    logger.info(json.dumps(format_stats(top_commenters), indent=2, ensure_ascii=False))
    
    # Получаем самые обсуждаемые посты
    most_commented = analyzer.get_most_commented_posts(channel_id)
    logger.info("\nСамые обсуждаемые посты:")
    logger.info(json.dumps(format_stats(most_commented), indent=2, ensure_ascii=False))
    
    # Получаем статистику по длине комментариев
    length_stats = analyzer.get_comment_length_stats(channel_id)
    logger.info("\nСтатистика по длине комментариев:")
    logger.info(json.dumps(format_stats(length_stats), indent=2, ensure_ascii=False))
    
    # Получаем статистику по реакциям
    reaction_stats = analyzer.get_reaction_stats(channel_id)
    logger.info("\nСтатистика по реакциям:")
    logger.info(json.dumps(format_stats(reaction_stats), indent=2, ensure_ascii=False))
    
    # Получаем статистику по пользователям, ставившим реакции
    user_reaction_stats = analyzer.get_user_reaction_stats(channel_id)
    logger.info("\nСтатистика по пользователям, ставившим реакции:")
    logger.info(json.dumps(format_stats(user_reaction_stats), indent=2, ensure_ascii=False))
    
    # Получаем топ пользователей по реакциям
    top_reaction_users = analyzer.get_top_reaction_users(channel_id)
    logger.info("\nТоп пользователей по реакциям:")
    logger.info(json.dumps(format_stats(top_reaction_users), indent=2, ensure_ascii=False))
    
    # Получаем список реакций
    reactions = analyzer.get_comment_reactions(channel_id)
    logger.info("\nСписок реакций:")
    logger.info(json.dumps(format_stats(reactions), indent=2, ensure_ascii=False))
    
    # Получаем комментарии с наибольшим количеством реакций
    most_reacted = analyzer.get_most_reacted_comments(channel_id)
    logger.info("\nКомментарии с наибольшим количеством реакций:")
    logger.info(json.dumps(format_stats(most_reacted), indent=2, ensure_ascii=False))
    
    # Получаем статистику по времени
    hourly_stats = analyzer.get_hourly_activity(channel_id)
    logger.info("\nСтатистика по часам (за последнюю неделю):")
    logger.info(json.dumps(format_stats(hourly_stats), indent=2, ensure_ascii=False))
    
    daily_stats = analyzer.get_daily_activity(channel_id)
    logger.info("\nСтатистика по дням (за последний месяц):")
    logger.info(json.dumps(format_stats(daily_stats), indent=2, ensure_ascii=False))

def main():
    logger.info("Запуск анализа комментариев")
    
    # Анализируем комментарии для каждого канала
    channels = CHANNEL_IDS if CHANNEL_IDS else [CHANNEL_USERNAME]
    for channel in channels:
        try:
            analyze_channel_comments(channel)
        except Exception as e:
            logger.error(f"Ошибка при анализе канала {channel}: {str(e)}", exc_info=True)
    
    logger.info("Анализ комментариев завершен")

if __name__ == "__main__":
    main() 