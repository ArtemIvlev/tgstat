from .database import Database

# Создаем глобальный экземпляр базы данных
_db = None

def get_db():
    """
    Возвращает экземпляр базы данных.
    Если экземпляр еще не создан, создает новый.
    """
    global _db
    if _db is None:
        _db = Database()
    return _db

__all__ = ['Database', 'get_db']
