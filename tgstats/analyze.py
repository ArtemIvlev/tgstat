from datetime import datetime, timedelta
from sqlalchemy import desc
from tgstats.database.database import Database
from tgstats.database.models import ChannelStats, ChannelActivity, DiscussionStats, ChannelParticipant
from tgstats.config.config import CHANNEL_TITLE
from tgstats.logger import get_logger

# Создаем логгер для этого модуля
logger = get_logger('analyze')

def analyze_subscribers_growth(days=30):
    """
    Анализирует рост подписчиков за указанный период
    """
    logger.info(f"Анализ роста подписчиков за последние {days} дней")
    db = Database()
    
    # Получаем статистику за последние N дней
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"Запрос данных с {start_date} по {end_date}")
    stats = db.query(ChannelStats).filter(
        ChannelStats.date >= start_date
    ).order_by(ChannelStats.date).all()
    
    if not stats:
        logger.warning(f"Нет данных о подписчиках за последние {days} дней")
        print(f"Нет данных о подписчиках за последние {days} дней")
        return
    
    logger.info(f"Найдено {len(stats)} записей о подписчиках")
    print(f"\nСтатистика роста подписчиков канала '{CHANNEL_TITLE}'")
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

def analyze_channel_activity(days=7):
    """
    Анализирует активность канала за указанный период
    """
    logger.info(f"Анализ активности канала за последние {days} дней")
    db = Database()
    
    # Получаем статистику за последние N дней
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"Запрос данных с {start_date} по {end_date}")
    stats = db.query(ChannelActivity).filter(
        ChannelActivity.date >= start_date
    ).order_by(ChannelActivity.date).all()
    
    if not stats:
        logger.warning(f"Нет данных об активности за последние {days} дней")
        print(f"Нет данных об активности за последние {days} дней")
        return
    
    logger.info(f"Найдено {len(stats)} записей об активности")
    print(f"\nСтатистика активности канала '{CHANNEL_TITLE}'")
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

def analyze_discussions(days=7):
    """
    Анализирует обсуждения канала за указанный период
    """
    logger.info(f"Анализ обсуждений канала за последние {days} дней")
    db = Database()
    
    # Получаем статистику за последние N дней
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"Запрос данных с {start_date} по {end_date}")
    stats = db.query(DiscussionStats).filter(
        DiscussionStats.date >= start_date
    ).order_by(DiscussionStats.date).all()
    
    if not stats:
        logger.warning(f"Нет данных об обсуждениях за последние {days} дней")
        print(f"Нет данных об обсуждениях за последние {days} дней")
        return
    
    logger.info(f"Найдено {len(stats)} записей об обсуждениях")
    print(f"\nСтатистика обсуждений канала '{CHANNEL_TITLE}'")
    print("=" * 50)
    
    for stat in stats:
        date_str = stat.date.strftime("%Y-%m-%d")
        print(f"\n{date_str}:")
        print(f"Всего комментариев: {stat.total_comments}")
        print(f"Активных пользователей: {stat.active_users}")
        
        # Показываем топ комментаторов
        if stat.top_commenters:
            print("\nТоп комментаторов:")
            for i, commenter in enumerate(stat.top_commenters, 1):
                print(f"{i}. Пользователь {commenter['user_id']}: {commenter['comments']} комментариев")
        
        # Показываем распределение комментариев по постам
        if stat.comments_per_post:
            print("\nРаспределение комментариев по постам:")
            for post_id, comments in stat.comments_per_post.items():
                print(f"Пост {post_id}: {comments} комментариев")

def analyze_top_users():
    """
    Анализирует и показывает наиболее активных пользователей канала
    """
    logger.info("Анализ наиболее активных пользователей канала")
    db = Database()
    
    # Получаем все записи о комментариях
    logger.info("Запрос всех записей о комментариях")
    stats = db.query(DiscussionStats).all()
    
    # Собираем статистику по пользователям
    user_stats = {}
    
    for stat in stats:
        if stat.top_commenters:
            for commenter in stat.top_commenters:
                user_id = commenter['user_id']
                comments = commenter['comments']
                
                if user_id not in user_stats:
                    user_stats[user_id] = {
                        'total_comments': 0,
                        'days_active': 0
                    }
                
                user_stats[user_id]['total_comments'] += comments
                user_stats[user_id]['days_active'] += 1
    
    if not user_stats:
        logger.warning("Нет данных об активности пользователей")
        print("\nНет данных об активности пользователей")
        return
    
    logger.info(f"Найдено {len(user_stats)} активных пользователей")
    
    # Получаем информацию о пользователях
    user_ids = list(user_stats.keys())
    logger.info(f"Запрос информации о {len(user_ids)} пользователях")
    users = db.query(ChannelParticipant).filter(
        ChannelParticipant.user_id.in_(user_ids)
    ).all()
    
    # Добавляем информацию о пользователях в статистику
    for user in users:
        if user.user_id in user_stats:
            user_stats[user.user_id]['username'] = user.username
            user_stats[user.user_id]['first_name'] = user.first_name
            user_stats[user.user_id]['last_name'] = user.last_name
    
    # Сортируем пользователей по количеству комментариев
    sorted_users = sorted(
        user_stats.items(),
        key=lambda x: x[1]['total_comments'],
        reverse=True
    )
    
    logger.info(f"Топ активных пользователей: {len(sorted_users)}")
    print("\nТоп активных пользователей:")
    print("=" * 50)
    
    for user_id, stats in sorted_users[:10]:  # Показываем топ-10
        name_parts = []
        if stats.get('first_name'):
            name_parts.append(stats['first_name'])
        if stats.get('last_name'):
            name_parts.append(stats['last_name'])
        name = ' '.join(name_parts) if name_parts else 'Неизвестно'
        
        username = f"@{stats['username']}" if stats.get('username') else 'нет юзернейма'
        
        print(f"\nПользователь: {name} ({username})")
        print(f"ID: {user_id}")
        print(f"Всего комментариев: {stats['total_comments']}")
        print(f"Дней активности: {stats['days_active']}")
        print(f"В среднем комментариев в день: {stats['total_comments'] / stats['days_active']:.1f}")

if __name__ == "__main__":
    logger.info("Запуск анализа статистики канала")
    analyze_subscribers_growth()
    print("\n" + "="*50 + "\n")
    analyze_channel_activity()
    print("\n" + "="*50 + "\n")
    analyze_discussions()
    print("\n" + "="*50 + "\n")
    analyze_top_users()
    logger.info("Анализ статистики канала завершен") 