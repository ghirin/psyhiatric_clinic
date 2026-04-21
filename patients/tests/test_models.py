
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from patients.models import Patient

import datetime

@pytest.mark.django_db
def test_patient_creation():
	user = get_user_model().objects.create(username='doctor', role='DOCTOR')
	patient = Patient.objects.create(
		last_name='Иванов',
		first_name='Иван',
		middle_name='Иванович',
		gender=Patient.Gender.MALE,
		birth_date=datetime.date(1990, 1, 1),
		address='г. Москва',
		admission_diagnosis='F20.0',
		admission_date=timezone.now(),
		attending_physician=user,
		created_by=user
	)
	assert patient.full_name == 'Иванов Иван Иванович'
	assert patient.age > 0
	assert patient.attending_physician == user

@pytest.mark.django_db
def test_patient_permissions():
	User = get_user_model()
	admin = User.objects.create(username='admin', role='ADMIN')
	doctor = User.objects.create(username='doc', role='DOCTOR')
	nurse = User.objects.create(username='nurse', role='NURSE')
	patient = Patient(
		last_name='Петров', first_name='Петр', birth_date=datetime.date(1990, 1, 1),
		admission_diagnosis='F20.0', admission_date=timezone.now(), created_by=admin, attending_physician=doctor
	)
	# Админ может всё
	assert patient.user_can_view(admin)
	assert patient.user_can_edit(admin)
	assert patient.user_can_delete(admin)
	# Врач может только своих
	assert patient.user_can_view(doctor)
	assert patient.user_can_edit(doctor)
	# Медсестра может только создавать
	assert patient.user_can_view(nurse)
	assert not patient.user_can_edit(nurse)