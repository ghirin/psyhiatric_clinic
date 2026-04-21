# patients/management/commands/update_case_numbers.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from patients.models import Patient
from datetime import datetime

class Command(BaseCommand):
    help = 'Обновляет номера историй болезни с 2024 на текущий год'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет изменено без сохранения',
        )
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Год для номеров карточек',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        target_year = options['year']
        
        self.stdout.write(f"Обновление номеров карточек на {target_year} год...")
        
        # Находим всех пациентов с номерами 2024-XXXX
        patients = Patient.objects.filter(case_number__startswith='2024-')
        
        if not patients.exists():
            self.stdout.write(self.style.WARNING("Пациентов с номерами 2024-XXXX не найдено"))
            return
        
        self.stdout.write(f"Найдено {patients.count()} пациентов для обновления")
        
        updated_count = 0
        errors = []
        
        for patient in patients:
            old_number = patient.case_number
            
            # Извлекаем номер после тире
            try:
                number_part = old_number.split('-')[1]
                new_number = f"{target_year}-{number_part}"
                
                # Проверяем не существует ли уже такой номер
                if Patient.objects.filter(case_number=new_number).exclude(pk=patient.pk).exists():
                    # Генерируем новый уникальный номер
                    last_case = Patient.objects.filter(
                        case_number__startswith=f'{target_year}-'
                    ).order_by('case_number').last()
                    
                    if last_case:
                        last_num = int(last_case.case_number.split('-')[1])
                        new_num = last_num + 1
                    else:
                        new_num = 1
                    
                    new_number = f"{target_year}-{new_num:04d}"
                
                if dry_run:
                    self.stdout.write(f"Будет обновлено: {old_number} → {new_number}")
                else:
                    patient.case_number = new_number
                    patient.save()
                    self.stdout.write(f"Обновлено: {old_number} → {new_number}")
                
                updated_count += 1
                
            except Exception as e:
                errors.append(f"Ошибка с пациентом {patient.pk} ({old_number}): {e}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\nDRY RUN: {updated_count} пациентов будут обновлены"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nУспешно обновлено: {updated_count} пациентов"
            ))
        
        if errors:
            self.stdout.write(self.style.ERROR("\nОшибки:"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  - {error}"))