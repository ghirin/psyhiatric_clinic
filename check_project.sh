#!/bin/bash
# Скрипт для проверки и миграции базы данных психиатрической больницы

cd /app

echo "=========================================="
echo "Проверка структуры проекта..."
echo "=========================================="

# Проверяем наличие необходимых файлов
echo ""
echo "Проверка файлов миграций..."
ls -la patients/migrations/

echo ""
echo "Проверка представлений..."
python -c "from patients.views_class_based import *; print('OK - представления загружены')"

echo ""
echo "Проверка моделей..."
python -c "from patients.models import *; print('OK - модели загружены')"

echo ""
echo "Проверка форм..."
python -c "from patients.forms import *; print('OK - формы загружены')"

echo ""
echo "Проверка URL..."
python -c "from patients.urls import *; print('OK - URL загружены')"

echo ""
echo "Проверка МКБ данных..."
python -c "from patients.mkb_data import get_mkb_codes; codes = get_mkb_codes(); print(f'OK - загружено {len(codes)} кодов МКБ')"

echo ""
echo "=========================================="
echo "Проверка завершена!"
echo "=========================================="

echo ""
echo "Для применения миграций выполните:"
echo "  python manage.py migrate"
echo ""
echo "Для запуска сервера:"
echo "  python manage.py runserver"
echo ""
echo "Горячие клавиши:"
echo "  N - Новый пациент"
echo "  S - Поиск пациента"
echo "  C - Календарь"
echo "  E - Экспорт"
echo "  H - Дашборд"
echo "  ? - Справка по горячим клавишам"