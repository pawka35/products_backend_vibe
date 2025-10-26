import secrets
import string
from typing import Optional

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Валидирует сложность пароля
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    
    if len(password) > 128:
        return False, "Пароль не должен превышать 128 символов"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not has_upper:
        return False, "Пароль должен содержать хотя бы одну заглавную букву"
    
    if not has_lower:
        return False, "Пароль должен содержать хотя бы одну строчную букву"
    
    if not has_digit:
        return False, "Пароль должен содержать хотя бы одну цифру"
    
    if not has_special:
        return False, "Пароль должен содержать хотя бы один специальный символ"
    
    # Проверка на простые пароли
    common_passwords = [
        "password", "123456", "qwerty", "admin", "letmein",
        "welcome", "monkey", "1234567890", "password123"
    ]
    
    if password.lower() in common_passwords:
        return False, "Пароль слишком простой, выберите более сложный"
    
    return True, ""

def generate_secure_password(length: int = 12) -> str:
    """Генерирует безопасный пароль"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Убеждаемся, что пароль соответствует требованиям
    is_valid, _ = validate_password_strength(password)
    if not is_valid:
        # Если не прошел валидацию, генерируем заново
        return generate_secure_password(length)
    
    return password
