from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from tgstats.database.models import Base
from tgstats.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

def get_table_columns(engine, table_name):
    """Получает список колонок существующей таблицы"""
    inspector = inspect(engine)
    return {col['name']: col for col in inspector.get_columns(table_name)}

def get_expected_columns(table):
    """Получает список ожидаемых колонок из таблицы"""
    return {c.name: c for c in table.columns}

def check_table_exists(engine, table_name):
    """Проверяет существование таблицы"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def check_schema_compatibility(engine):
    """Проверяет совместимость схемы базы данных с моделями"""
    logger.info("Проверка совместимости схемы базы данных")
    
    missing_tables = []
    incompatible_tables = []
    
    # Проверяем все таблицы из моделей
    for table_name, table in Base.metadata.tables.items():
        if not check_table_exists(engine, table_name):
            missing_tables.append(table_name)
            continue
            
        # Получаем текущие и ожидаемые колонки
        current_columns = get_table_columns(engine, table_name)
        expected_columns = get_expected_columns(table)
        
        # Проверяем наличие всех необходимых колонок
        missing_columns = set(expected_columns.keys()) - set(current_columns.keys())
        if missing_columns:
            incompatible_tables.append({
                'table': table_name,
                'missing_columns': list(missing_columns)
            })
    
    return {
        'missing_tables': missing_tables,
        'incompatible_tables': incompatible_tables
    }

def add_missing_columns(engine, table_name, missing_columns, table):
    """Добавляет отсутствующие колонки в таблицу"""
    try:
        with engine.begin() as connection:
            for column_name in missing_columns:
                column = table.columns[column_name]
                # Получаем тип колонки и значение по умолчанию
                col_type = column.type.compile(engine.dialect)
                
                # Специальная обработка для значений по умолчанию
                default = None
                if column.default:
                    if column.default.is_callable:
                        if column.default.arg == datetime.utcnow:
                            default = "CURRENT_TIMESTAMP"
                        else:
                            logger.warning(f"Неподдерживаемая функция по умолчанию для колонки {column_name}")
                    else:
                        default = column.default.arg
                
                # Формируем строку для значения по умолчанию
                default_str = f" DEFAULT {default}" if default is not None else ""
                
                # Формируем и выполняем SQL запрос
                sql = text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {col_type}{default_str}")
                connection.execute(sql)
                logger.info(f"Добавлена колонка {column_name} в таблицу {table_name}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при добавлении колонок в таблицу {table_name}: {str(e)}")
        return False

def update_schema(engine):
    """Безопасно обновляет схему базы данных"""
    logger.info("Начало обновления схемы базы данных")
    
    try:
        # Проверяем совместимость
        compatibility = check_schema_compatibility(engine)
        
        # Создаем отсутствующие таблицы
        if compatibility['missing_tables']:
            logger.info(f"Создание отсутствующих таблиц: {compatibility['missing_tables']}")
            Base.metadata.create_all(engine, tables=[Base.metadata.tables[table] for table in compatibility['missing_tables']])
        
        # Обновляем существующие таблицы
        for table_info in compatibility['incompatible_tables']:
            table_name = table_info['table']
            missing_columns = table_info['missing_columns']
            table = Base.metadata.tables[table_name]
            
            logger.info(f"Обновление таблицы {table_name}, добавление колонок: {missing_columns}")
            if not add_missing_columns(engine, table_name, missing_columns, table):
                return False
        
        logger.info("Схема базы данных успешно обновлена")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при обновлении схемы базы данных: {str(e)}")
        return False 