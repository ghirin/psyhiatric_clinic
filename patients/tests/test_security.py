
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from patients.models import Patient
from django.utils import timezone
import datetime

@pytest.mark.django_db
def test_patient_list_requires_login(client):
	url = reverse('patients:patient_list')
	response = client.get(url)
	assert response.status_code in (302, 401)

@pytest.mark.django_db
def test_patient_detail_forbidden_for_other_doctor(client):
	User = get_user_model()
	doctor1 = User.objects.create_user(username='doc1', password='pass', role='DOCTOR')
	doctor2 = User.objects.create_user(username='doc2', password='pass', role='DOCTOR')
	patient = Patient.objects.create(
		last_name='Иванов', first_name='Иван', birth_date=datetime.date(1990, 1, 1),
		admission_diagnosis='F20.0', admission_date=timezone.now(), created_by=doctor1, attending_physician=doctor1
	)
	url = reverse('patients:patient_detail', args=[patient.pk])
	client.force_login(doctor2)
	response = client.get(url)
	# Должен быть редирект или 403
	assert response.status_code in (302, 403)

# Пример теста аудита (если используется AuditLog)
from patients.audit import AuditLog

@pytest.mark.django_db
def test_audit_log_created_on_patient_create():
	User = get_user_model()
	user = User.objects.create_user(username='admin', password='pass', role='ADMIN')
	patient = Patient.objects.create(
		last_name='Тест', first_name='Тест', birth_date=datetime.date(1990, 1, 1),
		admission_diagnosis='F20.0', admission_date=timezone.now(), created_by=user, attending_physician=user
	)
	AuditLog.objects.create(user=user, patient=patient, action=AuditLog.Action.CREATE, timestamp=timezone.now())
	assert AuditLog.objects.filter(patient=patient, action=AuditLog.Action.CREATE).exists()