"""
Система логирования аудита для психиатрической больницы
Отслеживает: кто, когда и какие изменения внёс в карточку пациента
"""
import json
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

User = get_user_model()


class AuditLogManager(models.Manager):
    """Менеджер для работы с логами аудита"""
    
    def for_patient(self, patient_id):
        """Получить все логи для конкретного пациента"""
        return self.filter(patient_id=patient_id).order_by('-timestamp')
    
    def for_user(self, user_id):
        """Получить все действия конкретного пользователя"""
        return self.filter(user_id=user_id).order_by('-timestamp')
    
    def by_action(self, action):
        """Получить логи по типу действия"""
        return self.filter(action=action).order_by('-timestamp')
    
    def recent(self, days=7):
        """Получить логи за последние N дней"""
        from django.utils import timezone
        from datetime import timedelta
        return self.filter(
            timestamp__gte=timezone.now() - timedelta(days=days)
        ).order_by('-timestamp')


class AuditLog(models.Model):
    """Модель для хранения логов аудита"""
    
    class Action(models.TextChoices):
        CREATE = 'CREATE', 'Создание'
        VIEW = 'VIEW', 'Просмотр'
        UPDATE = 'UPDATE', 'Изменение'
        DELETE = 'Удаление'
        EXPORT = 'Экспорт'
        LOGIN = 'LOGIN', 'Вход в систему'
        LOGOUT = 'LOGOUT', 'Выход из системы'
        DISCHARGE = 'DISCHARGE', 'Выписка'
        ADMISSION = 'ADMISSION', 'Поступление'
        DOCUMENT_UPLOAD = 'DOCUMENT_UPLOAD', 'Загрузка документа'
        DOCUMENT_DELETE = 'DOCUMENT_DELETE', 'Удаление документа'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Пользователь'
    )
    
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пациент'
    )
    
    action = models.CharField(
        'Действие',
        max_length=20,
        choices=Action.choices
    )
    
    description = models.TextField('Описание действия')
    
    # Детали изменения (для отслеживания изменений полей)
    changed_fields = models.JSONField(
        'Изменённые поля',
        null=True,
        blank=True,
        help_text='JSON с информацией об изменённых полях'
    )
    
    # Метаданные
    ip_address = models.GenericIPAddressField(
        'IP-адрес',
        null=True,
        blank=True
    )
    
    user_agent = models.TextField(
        'User-Agent браузера',
        blank=True
    )
    
    timestamp = models.DateTimeField(
        'Время события',
        default=timezone.now
    )
    
    # Ссылка на объект
    object_type = models.CharField(
        'Тип объекта',
        max_length=50,
        blank=True
    )
    
    object_id = models.IntegerField(
        'ID объекта',
        null=True,
        blank=True
    )
    
    # Используем кастомный менеджер
    objects = AuditLogManager()
    
    class Meta:
        verbose_name = 'Лог аудита'
        verbose_name_plural = 'Логи аудита'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['patient', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        user_str = self.user.get_full_name() if self.user else 'Система'
        patient_str = self.patient.full_name if self.patient else 'N/A'
        return f"{user_str} - {self.get_action_display()} - {patient_str}"
    
    @property
    def changed_fields_display(self):
        """Возвращает читаемое представление изменённых полей"""
        if not self.changed_fields:
            return None
        
        if isinstance(self.changed_fields, str):
            try:
                self.changed_fields = json.loads(self.changed_fields)
            except:
                return self.changed_fields
        
        changes = []
        for field, values in self.changed_fields.items():
            if isinstance(values, dict) and 'old' in values and 'new' in values:
                changes.append(f"{field}: {values['old']} → {values['new']}")
            else:
                changes.append(f"{field}: {values}")
        
        return ", ".join(changes)


class AuditMiddleware:
    """
    Middleware для автоматического логирования действий пользователей
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Пропускаем статические файлы и медиа
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        
        # Пропускаем админку если нужно
        if request.path.startswith('/admin/'):
            return self.get_response(request)
        
        # Логируем только аутентифицированных пользователей
        if request.user.is_authenticated:
            # Логируем вход в систему
            if request.path == '/' and request.method == 'GET':
                # Это может быть загрузка страницы после входа
                pass
        
        response = self.get_response(request)
        return response


def log_action(
    user,
    action,
    description,
    patient=None,
    changed_fields=None,
    ip_address=None,
    user_agent=None,
    object_type=None,
    object_id=None
):
    """
    Утилита для создания записи лога аудита
    
    Args:
        user: Пользователь, совершивший действие
        action: Тип действия (CREATE, VIEW, UPDATE, DELETE, и т.д.)
        description: Описание действия
        patient: Пациент (опционально)
        changed_fields: Словарь изменённых полей (опционально)
        ip_address: IP адрес (опционально)
        user_agent: User-Agent браузера (опционально)
        object_type: Тип объекта (опционально)
        object_id: ID объекта (опционально)
    
    Returns:
        AuditLog: Созданный объект лога
    """
    log = AuditLog(
        user=user,
        patient=patient,
        action=action,
        description=description,
        changed_fields=changed_fields,
        ip_address=ip_address or get_client_ip(),
        user_agent=user_agent or get_user_agent(),
        object_type=object_type,
        object_id=object_id
    )
    log.save()
    return log


def get_client_ip(request=None):
    """Получение IP адреса клиента"""
    if request is None:
        return None
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request=None):
    """Получение User-Agent браузера"""
    if request is None:
        return None
    return request.META.get('HTTP_USER_AGENT', '')


def track_changes(instance, old_values=None, user=None, request=None):
    """
    Отслеживание изменений объекта
    
    Args:
        instance: Изменённый объект (Patient или другая модель)
        old_values: Словарь старых значений (опционально)
        user: Пользователь, внёсший изменения
        request: HTTP запрос (опционально)
    """
    if old_values is None:
        return
    
    changed_fields = {}
    for field, old_value in old_values.items():
        new_value = getattr(instance, field, None)
        if old_value != new_value:
            changed_fields[field] = {
                'old': str(old_value) if old_value else None,
                'new': str(new_value) if new_value else None
            }
    
    if changed_fields and user:
        log_action(
            user=user,
            action=AuditLog.Action.UPDATE,
            description=f'Изменение данных пациента',
            patient=instance if hasattr(instance, 'patient') else None,
            changed_fields=changed_fields,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            object_type=instance.__class__.__name__,
            object_id=instance.pk
        )


def get_patient_history(patient_id, limit=100):
    """
    Получение истории изменений пациента
    
    Args:
        patient_id: ID пациента
        limit: Максимальное количество записей
    
    Returns:
        QuerySet: Логи аудита для пациента
    """
    return AuditLog.objects.for_patient(patient_id)[:limit]


def get_user_activity(user_id, days=30):
    """
    Получение активности пользователя за период
    
    Args:
        user_id: ID пользователя
        days: Количество дней
    
    Returns:
        QuerySet: Логи аудита для пользователя
    """
    return AuditLog.objects.for_user(user_id).recent(days)


def get_daily_activity_report(date=None):
    """
    Получение отчёта активности за день
    
    Args:
        date: Дата (по умолчанию - сегодня)
    
    Returns:
        dict: Статистика за день
    """
    from datetime import datetime, timedelta
    from django.db.models import Count
    
    if date is None:
        date = timezone.now().date()
    
    start_of_day = datetime.combine(date, datetime.min.time())
    end_of_day = datetime.combine(date, datetime.max.time())
    
    stats = AuditLog.objects.filter(
        timestamp__range=[start_of_day, end_of_day]
    ).values('action').annotate(count=Count('id'))
    
    result = {}
    for item in stats:
        result[item['action']] = item['count']
    
    return {
        'date': date,
        'actions': result,
        'total': sum(result.values())
    }
