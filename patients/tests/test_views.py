
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from patients.models import Patient
from django.utils import timezone
import datetime

@pytest.mark.django_db
def test_patient_list_view(client):
	User = get_user_model()
	user = User.objects.create_user(username='admin', password='pass', role='ADMIN')
	client.force_login(user)
	url = reverse('patients:patient_list')
	response = client.get(url)
	assert response.status_code == 200
	assert 'patients_with_perms' in response.context

@pytest.mark.django_db
def test_patient_create_view(client):
	User = get_user_model()
	user = User.objects.create_user(username='doctor', password='pass', role='DOCTOR')
	client.force_login(user)
	url = reverse('patients:patient_create')
	data = {
		'last_name': 'Сидоров',
		'first_name': 'Сидор',
		'gender': 'M',
		'birth_date': '1990-01-01',
		'admission_diagnosis': 'F20.0',
		'admission_date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
		'address': 'г. Москва',
	}
	response = client.post(url, data)
	assert response.status_code in (302, 200)
	assert Patient.objects.filter(last_name='Сидоров').exists()

@pytest.mark.django_db
def test_patient_detail_permission(client):
	User = get_user_model()
	admin = User.objects.create_user(username='admin', password='pass', role='ADMIN')
	doctor = User.objects.create_user(username='doc', password='pass', role='DOCTOR')
	patient = Patient.objects.create(
		last_name='Иванов', first_name='Иван', birth_date=datetime.date(1990, 1, 1),
		admission_diagnosis='F20.0', admission_date=timezone.now(), created_by=admin, attending_physician=doctor
	)
	url = reverse('patients:patient_detail', args=[patient.pk])
	client.force_login(admin)
	response = client.get(url)
	assert response.status_code == 200