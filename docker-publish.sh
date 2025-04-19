#!/bin/bash

# Проверяем, авторизован ли пользователь в Docker Hub
if ! docker info | grep -q "Username"; then
    echo "Вы не авторизованы в Docker Hub. Выполните 'docker login'"
    exit 1
fi

# Собираем образ
echo "Сборка образа..."
docker build -t homo1udens/tgstat:latest .

# Публикуем образ
echo "Публикация образа в Docker Hub..."
docker push homo1udens/tgstat:latest

echo "Готово! Образ опубликован как homo1udens/tgstat:latest" 