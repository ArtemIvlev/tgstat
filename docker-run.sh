#!/bin/bash

# Проверяем наличие файла .env
if [ ! -f .env ]; then
    echo "Файл .env не найден. Создаем из примера..."
    cp .env.example .env
    echo "Пожалуйста, отредактируйте файл .env и добавьте необходимые данные"
    exit 1
fi

# Запускаем контейнер
docker-compose up --build -d

# Запускаем сбор статистики
docker-compose exec app python3 -m tgstats.run

# Запускаем анализ
docker-compose exec app python3 -m tgstats.analyze 