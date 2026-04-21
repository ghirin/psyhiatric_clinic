from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Count

from users.mixins import RoleRequiredMixin
from .models import Patient


class PatientCalendarView(RoleRequiredMixin, TemplateView):
    """Календарь поступлений и выписок пациентов"""
    template_name = 'patients/calendar.html'
    allowed_roles = ['ADMIN', 'DOCTOR', 'NURSE', 'REGISTRAR', 'ANALYST']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем параметры месяца
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        
        today = timezone.now().date()
        
        if year and month:
            try:
                year = int(year)
                month = int(month)
            except ValueError:
                year = today.year
                month = today.month
        else:
            year = today.year
            month = today.month
        
        # Получаем данные за месяц
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        # Поступления
        admissions = Patient.objects.filter(
            admission_date__gte=start_date,
            admission_date__lt=end_date
        ).select_related('attending_physician')
        
        # Выписки
        discharges = Patient.objects.filter(
            discharge_date__gte=start_date,
            discharge_date__lt=end_date,
            status='DISCHARGED'
        ).select_related('attending_physician')
        
        # Статистика за месяц
        month_stats = {
            'total_admissions': admissions.count(),
            'total_discharges': discharges.count(),
            'hospitalized_at_end': Patient.objects.filter(
                admission_date__lt=end_date,
                status='HOSPITALIZED'
            ).count(),
        }
        
        # Формируем события для календаря
        events = []
        
        for patient in admissions:
            events.append({
                'date': patient.admission_date,
                'type': 'admission',
                'title': f'Поступление: {patient.full_name}',
                'patient': patient,
                'icon': 'bi-arrow-down-circle',
                'color': 'success',
            })
        
        for patient in discharges:
            events.append({
                'date': patient.discharge_date,
                'type': 'discharge',
                'title': f'Выписка: {patient.full_name}',
                'patient': patient,
                'icon': 'bi-arrow-up-circle',
                'color': 'warning',
            })
        
        # Группируем события по дням
        events_by_day = {}
        for event in events:
            day = event['date'].day
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)
        
        # Информация о текущем месяце
        month_names = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        month_name = month_names[month - 1]
        
        # Генерация календаря
        calendar_weeks = self._generate_calendar(year, month, today, events_by_day)
        
        context.update({
            'calendar_weeks': calendar_weeks,
            'events_by_day': events_by_day,
            'year': year,
            'month': month,
            'month_name': month_name,
            'month_stats': month_stats,
            'prev_month': (month - 1) if month > 1 else 12,
            'prev_year': year if month > 1 else year - 1,
            'next_month': (month + 1) if month < 12 else 1,
            'next_year': year if month < 12 else year + 1,
        })
        
        return context
    
    def _generate_calendar(self, year, month, today, events_by_day):
        """Генерация календаря"""
        weeks = []
        
        # Первый день месяца
        first_day = date(year, month, 1)
        # День недели первого дня (0 = понедельник)
        weekday = first_day.weekday()
        
        # Начало календаря (понедельник недели, содержащей первый день месяца)
        if weekday == 6:  # воскресенье
            start_date = first_day
        else:
            start_date = first_day - timedelta(days=weekday + 1)
        
        # Генерируем 6 недель
        current_date = start_date
        for week_num in range(6):
            week = []
            for day_num in range(7):
                day_data = {
                    'day': current_date.day if current_date.month == month else None,
                    'is_today': current_date == today,
                    'date': current_date,
                }
                week.append(day_data)
                current_date += timedelta(days=1)
            
            weeks.append(week)
            
            # Если достигли следующего месяца и прошла хотя бы одна неделя
            if current_date.month != month and week_num >= 4:
                break
        
        return weeks


class QuickActionsView(LoginRequiredMixin, TemplateView):
    """Быстрые действия и горячие клавиши"""
    template_name = 'patients/quick_actions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем последних пациентов для быстрого доступа
        recent_patients = Patient.objects.order_by('-created_at')[:10]
        
        # Статистика для отображения
        today = timezone.now().date()
        
        stats = {
            'hospitalized_today': Patient.objects.filter(
                admission_date=today, 
                status='HOSPITALIZED'
            ).count(),
            'discharged_today': Patient.objects.filter(
                discharge_date=today, 
                status='DISCHARGED'
            ).count(),
            'total_hospitalized': Patient.objects.filter(
                status='HOSPITALIZED'
            ).count(),
        }
        
        # Информация о горячих клавишах
        hotkeys = [
            {'key': 'N', 'action': 'Создать пациента', 'url': 'patients:patient_create'},
            {'key': 'S', 'action': 'Поиск пациента', 'url': '#'},
            {'key': 'C', 'action': 'Календарь', 'url': 'patients:patient_calendar'},
            {'key': 'E', 'action': 'Экспорт', 'url': 'patients:patient_export'},
            {'key': 'H', 'action': 'Дашборд', 'url': 'patients:dashboard'},
            {'key': '?', 'action': 'Показать справку', 'url': '#hotkeys'},
        ]
        
        context.update({
            'recent_patients': recent_patients,
            'stats': stats,
            'hotkeys': hotkeys,
        })
        
        return context


class PatientQuickSearchView(LoginRequiredMixin, View):
    """Быстрый поиск пациента (AJAX)"""
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'results': []})
        
        # Поиск по ФИО, ИБ, телефону
        patients = Patient.objects.filter(
            Q(last_name__icontains=query) |
            Q(first_name__icontains=query) |
            Q(middle_name__icontains=query) |
            Q(case_number__icontains=query) |
            Q(phone__icontains=query)
        )[:10]
        
        results = [{
            'id': p.pk,
            'full_name': p.full_name,
            'case_number': p.case_number,
            'status': p.get_status_display(),
            'status_color': 'warning' if p.status == 'HOSPITALIZED' else 'success',
            'url': reverse_lazy('patients:patient_detail', kwargs={'pk': p.pk}),
        } for p in patients]
        
        return JsonResponse({'results': results})


class PatientMedicalNoteView(LoginRequiredMixin, TemplateView):
    """Создание медицинской записи с выбором шаблона"""
    template_name = 'patients/medical_note_form.html'
    
    def get(self, request, *args, **kwargs):
        patient = get_object_or_404(Patient, pk=kwargs['pk'])
        
        # Импорт внутри метода для избежания циклических импортов
        from .models import MedicalNoteTemplate
        templates = MedicalNoteTemplate.objects.filter(is_active=True)
        
        context = {
            'patient': patient,
            'templates': templates,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        patient = get_object_or_404(Patient, pk=kwargs['pk'])
        template_id = request.POST.get('template')
        content = request.POST.get('content', '')
        note_type = request.POST.get('note_type', 'PROGRESS')
        
        # Если выбран шаблон, заполняем плейсхолдеры
        if template_id:
            try:
                from .models import MedicalNoteTemplate
                template = MedicalNoteTemplate.objects.get(pk=template_id)
                content = template.fill_placeholders(patient, request.user)
            except MedicalNoteTemplate.DoesNotExist:
                pass
        
        messages.success(request, 'Запись создана')
        return redirect('patients:patient_detail', pk=patient.pk)


# Импорт для использования reverse_lazy
from django.urls import reverse_lazy
from django.db.models import Q