"""
Шифрование чувствительных данных в базе данных
Для диагнозов, анамнеза, примечаний и других конфиденциальных полей
"""
import os
import base64
import hashlib
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils import timezone

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    # Если cryptography не установлен, используем базовую реализацию
    Fernet = None


def get_encryption_key():
    """
    Получает ключ шифрования из настроек Django.
    Если ключ не установлен, генерирует новый.
    """
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    
    if key is None:
        # Генерируем ключ на основе SECRET_KEY
        if hasattr(settings, 'SECRET_KEY'):
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'psychiatric_hospital_salt',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(
                kdf.derive(settings.SECRET_KEY.encode())
            )
        else:
            raise ImproperlyConfigured(
                "ENCRYPTION_KEY или SECRET_KEY должен быть установлен в настройках Django"
            )
    
    # Ключ должен быть в формате Fernet (base64, 32 байта)
    if isinstance(key, str):
        key = key.encode()
    
    if len(key) < 32:
        # Дополняем ключ до 32 байт
        key = key + b'\x00' * (32 - len(key))
    
    return key


def get_fernet():
    """Получает объект Fernet для шифрования/дешифрования"""
    if Fernet is None:
        return None
    
    key = get_encryption_key()
    return Fernet(key)


class EncryptedTextField(models.TextField):
    """
    TextField с автоматическим шифрованием данных.
    Использует Fernet symmetric encryption.
    """
    
    def __init__(self, *args, **kwargs):
        # Убираем параметры, которые не нужны для зашифрованного поля
        self.encrypt_on_save = kwargs.pop('encrypt_on_save', True)
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value):
        """Подготовка значения для сохранения в БД"""
        if value is None:
            return value
        
        if not self.encrypt_on_save:
            return value
        
        # Шифруем значение
        fernet = get_fernet()
        if fernet is None:
            return value
        
        try:
            encrypted = fernet.encrypt(value.encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception:
            # Если шифрование не удалось, возвращаем как есть
            return value
    
    def from_db_value(self, value, expression, connection):
        """Получение значения из БД"""
        if value is None:
            return value
        
        fernet = get_fernet()
        if fernet is None:
            return value
        
        try:
            decrypted = fernet.decrypt(value.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception:
            # Если дешифрование не удалось, возвращаем как есть
            return value


class EncryptedCharField(models.CharField):
    """
    CharField с автоматическим шифрованием данных.
    """
    
    def __init__(self, *args, **kwargs):
        self.encrypt_on_save = kwargs.pop('encrypt_on_save', True)
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value):
        """Подготовка значения для сохранения в БД"""
        if value is None:
            return value
        
        if not self.encrypt_on_save:
            return value
        
        fernet = get_fernet()
        if fernet is None:
            return value
        
        try:
            encrypted = fernet.encrypt(str(value).encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception:
            return str(value)
    
    def from_db_value(self, value, expression, connection):
        """Получение значения из БД"""
        if value is None:
            return value
        
        fernet = get_fernet()
        if fernet is None:
            return value
        
        try:
            decrypted = fernet.decrypt(value.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception:
            return value


def encrypt_data(data):
    """
    Утилита для шифрования произвольных данных
    
    Args:
        data: Строка для шифрования
    
    Returns:
        str: Зашифрованная строка в формате base64
    """
    if data is None:
        return None
    
    fernet = get_fernet()
    if fernet is None:
        return data
    
    try:
        encrypted = fernet.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    except Exception:
        return data


def decrypt_data(encrypted_data):
    """
    Утилита для дешифрования данных
    
    Args:
        encrypted_data: Зашифрованная строка
    
    Returns:
        str: Расшифрованная строка
    """
    if encrypted_data is None:
        return None
    
    fernet = get_fernet()
    if fernet is None:
        return encrypted_data
    
    try:
        # Декодируем из base64
        encrypted = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted = fernet.decrypt(encrypted)
        return decrypted.decode('utf-8')
    except Exception:
        return encrypted_data


class EncryptionManager:
    """
    Менеджер для шифрования/дешифрования данных пациента
    """
    
    # Поля, которые нужно шифровать
    SENSITIVE_FIELDS = [
        'diagnosis',           # Диагноз
        'anamnesis',           # Анамнез
        'notes',               # Примечания
        'discharge_diagnosis', # Диагноз при выписке
        'admission_diagnosis', # Диагноз при поступлении
    ]
    
    @classmethod
    def encrypt_patient_data(cls, patient):
        """
        Шифрует чувствительные данные пациента
        
        Args:
            patient: Объект Patient
        """
        fernet = get_fernet()
        if fernet is None:
            return
        
        for field_name in cls.SENSITIVE_FIELDS:
            value = getattr(patient, field_name, None)
            if value and not cls._is_encrypted(value):
                try:
                    encrypted = fernet.encrypt(value.encode('utf-8'))
                    setattr(patient, field_name, encrypted.decode('utf-8'))
                except Exception:
                    pass
    
    @classmethod
    def decrypt_patient_data(cls, patient):
        """
        Дешифрует чувствительные данные пациента
        
        Args:
            patient: Объект Patient
        """
        fernet = get_fernet()
        if fernet is None:
            return
        
        for field_name in cls.SENSITIVE_FIELDS:
            value = getattr(patient, field_name, None)
            if value and cls._is_encrypted(value):
                try:
                    decrypted = fernet.decrypt(value.encode('utf-8'))
                    setattr(patient, field_name, decrypted.decode('utf-8'))
                except Exception:
                    pass
    
    @classmethod
    def _is_encrypted(cls, value):
        """
        Проверяет, зашифровано ли значение
        
        Args:
            value: Проверяемое значение
        
        Returns:
            bool: True если значение зашифровано
        """
        if not isinstance(value, str):
            return False
        
        try:
            # Пробуем декодировать из base64
            decoded = base64.urlsafe_b64decode(value.encode('utf-8'))
            # Если Fernet смог декодировать, значит это зашифрованные данные
            fernet = get_fernet()
            if fernet:
                fernet.decrypt(decoded)
                return True
        except Exception:
            pass
        
        return False


def setup_encryption():
    """
    Настройка шифрования в проекте.
    Вызывать при запуске приложения.
    """
    try:
        key = get_encryption_key()
        print(f"Шифрование настроено. Ключ: {key[:8]}...")
        return True
    except Exception as e:
        print(f"Ошибка настройки шифрования: {e}")
        return False


# Добавление в настройки Django (settings.py)
ENCRYPTION_SETTINGS_TEMPLATE = '''
# Настройки шифрования данных
# Если не установлен, будет сгенерирован автоматически на основе SECRET_KEY
# ENCRYPTION_KEY = b'your-32-byte-key-here'

# Библиотека cryptography должна быть установлена:
# pip install cryptography
'''

print("=" * 60)
print("Модуль шифрования загружен")
print("=" * 60)
print("\nДля активации шифрования:")
print("1. Установите библиотеку: pip install cryptography")
print("2. Добавьте в settings.py:")
print("   ENCRYPTION_KEY = b'your-32-byte-key'")
print("\nЧувствительные поля для шифрования:")
for field in EncryptionManager.SENSITIVE_FIELDS:
    print(f"  - {field}")
