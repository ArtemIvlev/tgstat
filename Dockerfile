FROM python:3.11-slim

LABEL maintainer="homo1udens"
LABEL description="Telegram channel statistics collector with scheduler"
LABEL version="1.0"
LABEL org.opencontainers.image.source="https://github.com/homo1udens/tgstat"
LABEL org.opencontainers.image.licenses="MIT"

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .
COPY tgstats/ tgstats/
COPY README.md .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Создание пользователя без прав root
RUN useradd -m tgstats && \
    chown -R tgstats:tgstats /app

USER tgstats

# Установка переменных окружения
ENV PYTHONPATH=/app
ENV TG_API_ID=${TG_API_ID}
ENV TG_API_HASH=${TG_API_HASH}
ENV TG_DB_URL=${TG_DB_URL}
ENV TG_CHANNEL_ID=${TG_CHANNEL_ID}
ENV TG_CHANNEL_TITLE=${TG_CHANNEL_TITLE}
ENV SESSION_PATH=/data/tg-post.session

# Запуск приложения
CMD ["python", "-m", "tgstats.scheduler"] 