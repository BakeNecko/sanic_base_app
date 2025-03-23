import os
from sanic.config import Config


class DevConfig(Config):
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgresql')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'mydatabase')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'myuser')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'mypassword')

    SECRET_KEY = os.getenv('SECRET_KEY', 'gfdmhghif38yrf9ew0jkf32')
    ALGO = os.getenv('ALGO', 'HS256')
    HASH_ALGO = os.getenv('HASH_ALGO', 'SHA256')
    # 2 week
    REFRESH_TOKEN_EXPIRE_DELTA = os.getenv('REFRESH_TOKEN_EXPIRE_DELTA', 60 * 60 * 24 * 14)
    # 15 min
    ACCESS_TOKEN_EXPIRE_DELTA = os.getenv('ACCESS_TOKEN_EXPIRE_DELTA', 60 * 15)
    LOG_LEVEL = os.getenv('LOG_LEVEL', default='DEBUG')

class PytestConfig(DevConfig):
    POSTGRES_HOST = os.getenv('PYTEST_POSTGRES_HOST', 'postgresql_pytest')
    POSTGRES_DB = os.getenv('PYTEST_POSTGRES_DB', 'pytestdb')
    POSTGRES_USER = os.getenv('PYTEST_POSTGRES_USER', 'pytestuser')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'mypassword')
    