#!/bin/bash
# Скрипт для применения миграций

cd /app

# Применяем миграции
echo "Применение миграций..."
python manage.py migrate patients

echo "Миграции применены успешно!"