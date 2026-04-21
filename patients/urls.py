from django.urls import path
from .views_class_based import (
    DashboardView,
    PatientListView,
    PatientDetailView,
    PatientCreateView,
    PatientUpdateView,
    PatientDeleteView,
    PatientDischargeView,
    PatientExportView,
    PatientClearFiltersView,
    ApiDiagnosesView,
)
from .views_calendar import (
    PatientCalendarView,
    QuickActionsView,
    PatientQuickSearchView,
    PatientMedicalNoteView,
)
from .mkb_data import ApiMKBAutocomplete

app_name = 'patients'

urlpatterns = [
    # Основные маршруты
    path('', DashboardView.as_view(), name='dashboard'),
    path('patients/', PatientListView.as_view(), name='patient_list'),
    path('patients/create/', PatientCreateView.as_view(), name='patient_create'),
    path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient_detail'),
    path('patients/<int:pk>/edit/', PatientUpdateView.as_view(), name='patient_update'),
    path('patients/<int:pk>/delete/', PatientDeleteView.as_view(), name='patient_delete'),
    path('patients/<int:pk>/discharge/', PatientDischargeView.as_view(), name='patient_discharge'),
    path('patients/<int:pk>/note/', PatientMedicalNoteView.as_view(), name='patient_note'),
    
    # Экспорт
    path('patients/export/', PatientExportView.as_view(), name='patient_export'),
    
    # Календарь
    path('patients/calendar/', PatientCalendarView.as_view(), name='patient_calendar'),
    
    # Очистка фильтров
    path('patients/clear-filters/', PatientClearFiltersView.as_view(), name='patient_clear_filters'),
    
    # Быстрые действия
    path('quick-actions/', QuickActionsView.as_view(), name='quick_actions'),
    
    # API
    path('api/diagnoses/', ApiDiagnosesView.as_view(), name='api_diagnoses'),
    path('api/patient/search/', PatientQuickSearchView.as_view(), name='api_patient_search'),
    path('api/mkb/autocomplete/', ApiMKBAutocomplete.as_view(), name='api_mkb_autocomplete'),
]