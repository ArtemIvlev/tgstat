from datetime import datetime, timedelta
from sqlalchemy import desc, func, create_engine, text
from sqlalchemy.orm import sessionmaker
from tgstats.database import get_db
from tgstats.database.models import ChannelStats, ChannelPost, ChannelParticipant, ChannelActivity, DiscussionStats, HourlyActivity, Base
from tgstats.config.config import CHANNEL_IDS
from tgstats.logger import get_logger
from tgstats.config import PG_CONNECTION_PARAMS
import json

# Создаем логгер для этого модуля
logger = get_logger(__name__)

def get_channel_title(channel_id):
    """Получает название канала из базы данных"""
    db = get_db()
    # Пытаемся получить самую последнюю запись статистики для канала
    stats = db.query(ChannelStats).filter(
        ChannelStats.channel_id == channel_id
    ).order_by(desc(ChannelStats.date)).first()
    
    # Если запись найдена и у нее есть название, возвращаем его
    if stats and stats.title:
        return stats.title
    
    # Если не нашли запись или название пустое, возвращаем ID канала
    return f"Канал {channel_id}"

def analyze_subscribers_growth(channel_id=None, days=30):
    """
    Анализирует рост подписчиков за указанный период
    """
    channel_id = channel_id or CHANNEL_IDS[0]
    channel_title = get_channel_title(channel_id)
    logger.info(f"Анализ роста подписчиков за последние {days} дней для канала {channel_id}")
    db = get_db()
    
    # Получаем статистику за последние N дней
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"Запрос данных с {start_date} по {end_date}")
    stats = db.query(ChannelStats).filter(
        ChannelStats.date >= start_date,
        ChannelStats.channel_id == channel_id
    ).order_by(ChannelStats.date).all()
    
    if not stats:
        logger.warning(f"Нет данных о подписчиках за последние {days} дней")
        print(f"Нет данных о подписчиках за последние {days} дней")
        return
    
    logger.info(f"Найдено {len(stats)} записей о подписчиках")
    print(f"\nСтатистика роста подписчиков канала '{channel_title}'")
    print("=" * 50)
    
    prev_subscribers = None
    for stat in stats:
        date_str = stat.date.strftime("%Y-%m-%d %H:%M")
        growth = ""
        if prev_subscribers is not None:
            diff = stat.subscribers - prev_subscribers
            if diff > 0:
                growth = f"+{diff}"
            elif diff < 0:
                growth = f"{diff}"
            else:
                growth = "0"
            growth = f" ({growth})"
        
        print(f"{date_str}: {stat.subscribers}{growth}")
        prev_subscribers = stat.subscribers

def analyze_channel_activity(channel_id=None, days=7):
    """
    Анализирует активность канала за указанный период
    """
    channel_id = channel_id or CHANNEL_IDS[0]
    channel_title = get_channel_title(channel_id)
    logger.info(f"Анализ активности канала {channel_id} за последние {days} дней")
    db = get_db()
    
    # Получаем статистику за последние N дней
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"Запрос данных с {start_date} по {end_date}")
    stats = db.query(ChannelActivity).filter(
        ChannelActivity.date >= start_date,
        ChannelActivity.channel_id == channel_id
    ).order_by(ChannelActivity.date).all()
    
    if not stats:
        logger.warning(f"Нет данных об активности за последние {days} дней")
        print(f"Нет данных об активности за последние {days} дней")
        return
    
    logger.info(f"Найдено {len(stats)} записей об активности")
    print(f"\nСтатистика активности канала '{channel_title}'")
    print("=" * 50)
    
    for stat in stats:
        date_str = stat.date.strftime("%Y-%m-%d")
        print(f"\n{date_str}:")
        print(f"Просмотров: {stat.total_views}")
        print(f"Репостов: {stat.total_forwards}")
        print(f"Реакций: {stat.total_reactions}")
        print(f"Постов: {stat.posts_count}")
        
        # Показываем активность по часам
        if stat.active_hours:
            print("\nАктивность по часам:")
            for hour, views in sorted(stat.active_hours.items()):
                print(f"{hour}:00 - {views} просмотров")

def analyze_discussions(channel_id=None, days=7):
    """
    Анализирует обсуждения канала за указанный период
    """
    channel_id = channel_id or CHANNEL_IDS[0]
    channel_title = get_channel_title(channel_id)
    logger.info(f"Анализ обсуждений канала {channel_id} за последние {days} дней")
    db = get_db()
    
    # Получаем статистику за последние N дней
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"Запрос данных с {start_date} по {end_date}")
    stats = db.query(DiscussionStats).filter(
        DiscussionStats.date >= start_date,
        DiscussionStats.channel_id == channel_id
    ).order_by(DiscussionStats.date).all()
    
    if not stats:
        logger.warning(f"Нет данных об обсуждениях за последние {days} дней")
        print(f"Нет данных об обсуждениях за последние {days} дней")
        return
    
    logger.info(f"Найдено {len(stats)} записей об обсуждениях")
    print(f"\nСтатистика обсуждений канала '{channel_title}'")
    print("=" * 50)
    
    for stat in stats:
        date_str = stat.date.strftime("%Y-%m-%d")
        print(f"\n{date_str}:")
        print(f"Всего комментариев: {stat.total_comments}")
        print(f"Активных пользователей: {stat.active_users}")
        
        if stat.comments_per_post:
            print("\nКомментарии по постам:")
            for post_id, comments in stat.comments_per_post.items():
                print(f"Пост {post_id}: {comments} комментариев")
        
        if stat.top_commenters:
            print("\nТоп комментаторов:")
            for i, commenter in enumerate(stat.top_commenters, 1):
                print(f"{i}. Пользователь {commenter['user_id']}: {commenter['comments']} комментариев")

def analyze_top_users(channel_id=None):
    """
    Анализирует топ пользователей по активности
    """
    channel_id = channel_id or CHANNEL_IDS[0]
    channel_title = get_channel_title(channel_id)
    logger.info(f"Анализ топ пользователей канала {channel_id}")
    db = get_db()
    
    # Получаем всех участников
    participants = db.query(ChannelParticipant).filter(
        ChannelParticipant.channel_id == channel_id
    ).all()
    
    if not participants:
        logger.warning("Нет данных об участниках")
        print("Нет данных об участниках")
        return
    
    logger.info(f"Найдено {len(participants)} участников")
    print(f"\nТоп пользователей канала '{channel_title}'")
    print("=" * 50)
    
    # Группируем по наличию username и phone
    stats = {
        'с username': 0,
        'с телефоном': 0,
        'с именем': 0,
        'с фамилией': 0,
        'удалённые': 0,
        'боты': 0,
        'верифицированные': 0
    }
    
    for participant in participants:
        raw = participant.raw
        if raw:
            raw_data = json.loads(raw) if isinstance(raw, str) else raw
            if raw_data.get('username'):
                stats['с username'] += 1
            if raw_data.get('phone'):
                stats['с телефоном'] += 1
            if raw_data.get('first_name'):
                stats['с именем'] += 1
            if raw_data.get('last_name'):
                stats['с фамилией'] += 1
            if raw_data.get('deleted'):
                stats['удалённые'] += 1
            if raw_data.get('bot'):
                stats['боты'] += 1
            if raw_data.get('verified'):
                stats['верифицированные'] += 1
    
    # Выводим статистику
    print("\nСтатистика пользователей:")
    for category, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"{category}: {count} ({count/len(participants)*100:.1f}%)")
            
    # Выводим топ-10 пользователей с username
    print("\nТоп-10 пользователей с username:")
    top_users = [p for p in participants if p.username][:10]
    for i, user in enumerate(top_users, 1):
        name_parts = []
        if user.first_name:
            name_parts.append(user.first_name)
        if user.last_name:
            name_parts.append(user.last_name)
        name = ' '.join(name_parts) if name_parts else 'Без имени'
        print(f"{i}. @{user.username} ({name})")

def analyze_hourly_activity(channel_id=None):
    """
    Анализирует почасовую активность
    """
    channel_id = channel_id or CHANNEL_IDS[0]
    channel_title = get_channel_title(channel_id)
    logger.info(f"Анализ почасовой активности канала {channel_id}")
    db = get_db()
    
    # Получаем последнюю запись активности
    activity = db.query(ChannelActivity).filter(
        ChannelActivity.channel_id == channel_id
    ).order_by(desc(ChannelActivity.date)).first()
    
    if not activity:
        logger.warning("Нет данных о почасовой активности")
        print("Нет данных о почасовой активности")
        return
    
    print(f"\nПочасовая активность канала '{channel_title}'")
    print("=" * 50)
    print(f"Дата: {activity.date.strftime('%Y-%m-%d')}")
    
    # Выводим статистику по часам
    if activity.active_hours:
        for hour in range(24):
            hour_str = f"{hour:02d}:00"
            views = activity.active_hours.get(str(hour), 0)
            
            if views > 0:
                print(f"\n{hour_str}:")
                print(f"Просмотров: {views}")
                
                # Если есть данные о репостах и реакциях, выводим их
                if hasattr(activity, 'forwards_by_hour') and activity.forwards_by_hour:
                    forwards = activity.forwards_by_hour.get(str(hour), 0)
                    print(f"Репостов: {forwards}")
                    
                if hasattr(activity, 'reactions_by_hour') and activity.reactions_by_hour:
                    reactions = activity.reactions_by_hour.get(str(hour), 0)
                    print(f"Реакций: {reactions}")
                    
                if hasattr(activity, 'posts_by_hour') and activity.posts_by_hour:
                    posts = activity.posts_by_hour.get(str(hour), 0)
                    print(f"Постов: {posts}")
    else:
        print("\nНет данных о просмотрах по часам")

def analyze_daily_trends(channel_id=None):
    """
    Анализирует ежедневные тренды
    """
    channel_id = channel_id or CHANNEL_IDS[0]
    channel_title = get_channel_title(channel_id)
    logger.info(f"Анализ ежедневных трендов канала {channel_id}")
    db = get_db()
    
    # Получаем статистику за последние 7 дней
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    # Получаем статистику подписчиков
    stats = db.query(ChannelStats).filter(
        ChannelStats.date >= start_date,
        ChannelStats.channel_id == channel_id
    ).order_by(ChannelStats.date).all()
    
    # Получаем статистику активности
    activity = db.query(ChannelActivity).filter(
        ChannelActivity.date >= start_date,
        ChannelActivity.channel_id == channel_id
    ).order_by(ChannelActivity.date).all()
    
    if not stats and not activity:
        logger.warning("Нет данных о трендах")
        print("Нет данных о трендах")
        return
    
    print(f"\nЕжедневные тренды канала '{channel_title}'")
    print("=" * 50)
    
    # Создаем словарь для объединения данных по датам
    daily_stats = {}
    
    # Добавляем данные о подписчиках
    for stat in stats:
        date_str = stat.date.strftime("%Y-%m-%d")
        if date_str not in daily_stats:
            daily_stats[date_str] = {'date': stat.date}
        daily_stats[date_str]['subscribers'] = stat.subscribers
    
    # Добавляем данные об активности
    for act in activity:
        date_str = act.date.strftime("%Y-%m-%d")
        if date_str not in daily_stats:
            daily_stats[date_str] = {'date': act.date}
        daily_stats[date_str]['views'] = act.total_views
        daily_stats[date_str]['forwards'] = act.total_forwards
        daily_stats[date_str]['reactions'] = act.total_reactions
        daily_stats[date_str]['posts'] = act.posts_count
    
    # Выводим статистику по дням
    for date_str, data in sorted(daily_stats.items()):
        print(f"\n{date_str}:")
        if 'subscribers' in data:
            print(f"Подписчиков: {data['subscribers']}")
        if 'views' in data:
            print(f"Просмотров: {data['views']}")
        if 'forwards' in data:
            print(f"Репостов: {data['forwards']}")
        if 'reactions' in data:
            print(f"Реакций: {data['reactions']}")
        if 'posts' in data:
            print(f"Постов: {data['posts']}")

def analyze_data(channel_ids=None):
    """Запускает все виды анализа для каждого канала"""
    
    # Если каналы не указаны, берем из конфигурации
    if not channel_ids:
        channel_ids = CHANNEL_IDS
    
    logger.info(f"Запуск анализа данных для каналов: {channel_ids}")
    
    if not channel_ids:
        logger.warning("Список каналов для анализа пуст")
        return
        
    for channel_id in channel_ids:
        try:
            # Получаем название канала
            channel_title = get_channel_title(channel_id)
            logger.info(f"Анализ данных для канала {channel_id} (название: {channel_title})")
            
            # Проверяем наличие данных о канале
            db = get_db()
            stats = db.query(ChannelStats).filter(
                ChannelStats.channel_id == channel_id
            ).order_by(desc(ChannelStats.date)).first()
            
            if not stats:
                logger.warning(f"Нет данных о канале {channel_id} в базе данных")
                continue
                
            print(f"\n{'='*20} Канал {channel_title} {'='*20}")
            
            # Запускаем все виды анализа
            analyze_subscribers_growth(channel_id)
            analyze_channel_activity(channel_id)
            analyze_discussions(channel_id)
            analyze_top_users(channel_id)
            analyze_hourly_activity(channel_id)
            analyze_daily_trends(channel_id)
        except Exception as e:
            logger.error(f"Ошибка при анализе канала {channel_id}: {str(e)}", exc_info=True)

def main():
    """Основная функция для запуска анализа"""
    analyze_data()

if __name__ == "__main__":
    main() 