import schedule
import time
import asyncio
import signal
import sys
from datetime import datetime
from tgstats.run import main as run_collector
from tgstats.analyze import analyze_data
from tgstats.run_gender import main as run_gender_analysis
from tgstats.collect_comments import collect_comments
from tgstats.logger import get_logger
from tgstats.database.database import Database

logger = get_logger(__name__)

# Глобальная переменная для контроля выполнения
is_running = True

def signal_handler(signum, frame):
    """Обработчик сигналов завершения"""
    global is_running
    logger.info(f"Получен сигнал {signum}, завершение работы...")
    is_running = False

async def run_collector_job():
    """Запуск сбора данных"""
    logger.info("Запуск сбора данных по расписанию")
    try:
        await run_collector()
    except Exception as e:
        logger.error(f"Ошибка при сборе данных: {str(e)}", exc_info=True)

async def run_analyzer_job():
    """Запуск анализа данных"""
    logger.info("Запуск анализа данных по расписанию")
    try:
        analyze_data()
    except Exception as e:
        logger.error(f"Ошибка при анализе данных: {str(e)}", exc_info=True)

async def run_gender_job():
    """Запуск анализа гендеров участников"""
    logger.info("Запуск анализа гендеров участников по расписанию")
    try:
        await run_gender_analysis()
    except Exception as e:
        logger.error(f"Ошибка при анализе гендеров: {str(e)}", exc_info=True)

async def run_comments_collector_job():
    """Запуск сбора комментариев"""
    logger.info("Запуск сбора комментариев по расписанию")
    try:
        await collect_comments()
    except Exception as e:
        logger.error(f"Ошибка при сборе комментариев: {str(e)}", exc_info=True)

def run_collector_wrapper():
    """Обертка для запуска асинхронного сбора данных"""
    try:
        asyncio.run(run_collector_job())
    except Exception as e:
        logger.error(f"Ошибка в обертке сбора данных: {str(e)}", exc_info=True)

def run_analyzer_wrapper():
    """Обертка для запуска анализа данных"""
    try:
        asyncio.run(run_analyzer_job())
    except Exception as e:
        logger.error(f"Ошибка в обертке анализа данных: {str(e)}", exc_info=True)

def run_gender_wrapper():
    """Обертка для запуска анализа гендеров"""
    try:
        asyncio.run(run_gender_job())
    except Exception as e:
        logger.error(f"Ошибка в обертке анализа гендеров: {str(e)}", exc_info=True)

def run_comments_collector_wrapper():
    """Обертка для запуска сбора комментариев"""
    try:
        asyncio.run(run_comments_collector_job())
    except Exception as e:
        logger.error(f"Ошибка в обертке сбора комментариев: {str(e)}", exc_info=True)

def main():
    """Основная функция планировщика"""
    global is_running
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Запуск планировщика задач")
    
    # Сбор данных каждый час
    schedule.every().hour.at(":00").do(run_collector_wrapper)
    
    # Сбор комментариев каждый час в 30 минут
    schedule.every().hour.at(":30").do(run_comments_collector_wrapper)
    
    # Анализ гендеров каждый день в 03:00
    schedule.every().day.at("03:00").do(run_gender_wrapper)
    
    # Запуск цикла проверки расписания
    while is_running:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            logger.error(f"Ошибка в основном цикле планировщика: {str(e)}", exc_info=True)
            time.sleep(60)  # Пауза перед следующей попыткой
    
    logger.info("Планировщик остановлен")

if __name__ == "__main__":
    main() 