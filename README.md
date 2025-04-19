# Telegram Channel Statistics Collector

Контейнер для сбора и анализа статистики Telegram-каналов.

## Возможности

- Сбор базовой статистики канала (подписчики, посты, просмотры)
- Сбор статистики активности по часам
- Сбор статистики обсуждений
- Автоматический сбор данных по расписанию
- Сохранение данных в PostgreSQL

## Расписание

- Ежедневно в 00:00 - сбор базовой статистики
- Каждое воскресенье в 01:00 - полный сбор данных
- Каждое воскресенье в 02:00 - анализ собранных данных

## Использование

1. Создайте файл `.env` с необходимыми переменными окружения:

```env
# Telegram API credentials
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash

# Database configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=tgstat
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_password

# Channel configuration
TG_CHANNEL_ID=your_channel_id
TG_CHANNEL_TITLE=your_channel_title
```

2. Запустите контейнер:

```bash
docker run -d \
  --name tgstat \
  --env-file .env \
  -v /path/to/session:/app/session \
  homo1udens/tgstat:latest
```

## Переменные окружения

| Переменная | Описание | Обязательная |
|------------|----------|--------------|
| TG_API_ID | ID приложения Telegram | Да |
| TG_API_HASH | Hash приложения Telegram | Да |
| POSTGRES_HOST | Хост PostgreSQL | Да |
| POSTGRES_PORT | Порт PostgreSQL | Да |
| POSTGRES_DB | Имя базы данных | Да |
| POSTGRES_USER | Пользователь PostgreSQL | Да |
| POSTGRES_PASSWORD | Пароль PostgreSQL | Да |
| TG_CHANNEL_ID | ID канала Telegram | Да |
| TG_CHANNEL_TITLE | Название канала | Да |

## Лицензия

MIT 