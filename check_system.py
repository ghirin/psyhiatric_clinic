#!/usr/bin/env python
"""
Проверка и запуск сервера психиатрической больницы
"""
import os
import sys

# Добавляем путь проекта
sys.path.insert(0, '/app')
os.chdir('/app')

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'psychiatric_hospital.settings')

import django
django.setup()

def check_system():
    """Проверка системы перед запуском"""
    print("=" * 60)
    print("Психиатрическая больница - Проверка системы")
    print("=" * 60)
    
    errors = []
    
    # Проверка моделей
    print("\n[1/6] Проверка моделей...")
    try:
        from patients.models import Patient, Hospitalization, Diagnosis
        print("  ✓ Модель Patient загружена")
        print("  ✓ Модель Hospitalization загружена")
        print("  ✓ Модель Diagnosis загружена")
    except Exception as e:
        errors.append(f"Ошибка загрузки моделей: {e}")
        print(f"  ✗ Ошибка: {e}")
    
    # Проверка представлений
    print("\n[2/6] Проверка представлений...")
    try:
        from patients.views_class_based import (
            DashboardView, PatientListView, PatientDetailView,
            PatientCreateView, PatientUpdateView, PatientDeleteView,
            PatientDischargeView, PatientExportView, PatientClearFiltersView,
            ApiDiagnosesView, PatientStatisticsView,
            HospitalizationCreateView, HospitalizationUpdateView, HospitalizationDeleteView
        )
        print("  ✓ Основные представления загружены")
    except Exception as e:
        errors.append(f"Ошибка загрузки представлений: {e}")
        print(f"  ✗ Ошибка: {e}")
    
    try:
        from patients.views_calendar import (
            PatientCalendarView, QuickActionsView,
            PatientQuickSearchView, PatientMedicalNoteView
        )
        print("  ✓ Представления календаря загружены")
    except Exception as e:
        errors.append(f"Ошибка загрузки представлений календаря: {e}")
        print(f"  ✗ Ошибка: {e}")
    
    # Проверка форм
    print("\n[3/6] Проверка форм...")
    try:
        from patients.forms import PatientForm, PatientSearchForm, PatientExportForm
        print("  ✓ Формы загружены")
    except Exception as e:
        errors.append(f"Ошибка загрузки форм: {e}")
        print(f"  ✗ Ошибка: {e}")
    
    # Проверка URL
    print("\n[4/6] Проверка URL...")
    try:
        from patients.urls import urlpatterns
        print(f"  ✓ URL загружены ({len(urlpatterns)} маршрутов)")
    except Exception as e:
        errors.append(f"Ошибка загрузки URL: {e}")
        print(f"  ✗ Ошибка: {e}")
    
    # Проверка МКБ
    print("\n[5/6] Проверка базы МКБ...")
    try:
        from patients.mkb_data import get_mkb_codes
        codes = get_mkb_codes()
        print(f"  ✓ База МКБ загружена ({len(codes)} кодов)")
    except Exception as e:
        errors.append(f"Ошибка загрузки МКБ: {e}")
        print(f"  ✗ Ошибка: {e}")
    
    # Проверка миграций
    print("\n[6/6] Проверка миграций...")
    try:
        from django.core.management import call_command
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM patients_patient")
            count = cursor.fetchone()[0]
            print(f"  ✓ Пациентов в базе: {count}")
    except Exception as e:
        print(f"  ⚠ Предупреждение: {e}")
    
    # Итог
    print("\n" + "=" * 60)
    if errors:
        print("ОШИБКИ ОБНАРУЖЕНЫ:")
        for error in errors:
            print(f"  ✗ {error}")
        return False
    else:
        print("Все проверки пройдены успешно!")
        print("\nГорячие клавиши:")
        print("  N - Новый пациент")
        print("  S - Поиск пациента")
        print("  C - Календарь")
        print("  E - Экспорт")
        print("  H - Дашборд")
        print("  ? - Справка")
        return True

if __name__ == '__main__':
    success = check_system()
    sys.exit(0 if success else 1)
