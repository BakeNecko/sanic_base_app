from functools import lru_cache
from datetime import datetime, timezone
import hashlib

import bcrypt


def utc_now():
    return datetime.now(tz=timezone.utc)

def timezone_now():
    return int(utc_now().timestamp())

@lru_cache(maxsize=100)
def hash_password(password: str) -> str:
    """Хеширование пароля с использованием HMAC и секретного ключа."""
    return  bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def get_signature(signature_string: str) -> str:
    return hashlib.sha256(signature_string.encode()).hexdigest()

def get_limit_offset_params(params: dict):
    return params.get('limit', 50), params.get('offset', 0)
