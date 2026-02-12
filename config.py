"""
Глобальные настройки сервиса.

Здесь задаются хосты и порты для:
- FastAPI / uvicorn API
- локального ComfyUI сервера
- MongoDB (значения берутся из переменных окружения /.env)
"""

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Загружаем .env в переменные окружения до чтения настроек
load_dotenv()

# Настройки HTTP API (FastAPI / uvicorn)
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8001"))

# Настройки локального ComfyUI сервера
COMFYUI_HOST: str = os.getenv("COMFYUI_HOST", "localhost")
COMFYUI_PORT: int = int(os.getenv("COMFYUI_PORT", "8000"))

# Настройки MongoDB
MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT: int = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "comfyui")
MONGO_USER: str = os.getenv("MONGO_USER", "root")
MONGO_PASSWORD: str = os.getenv("MONGO_PASSWORD", "root_password_change_me")


def get_mongo_uri() -> str:
    """
    Возвращает URI подключения к MongoDB по переменным окружения.
    Формат: mongodb://user:password@host:port/db
    Логин и пароль кодируются через quote_plus (спецсимволы @, :, /, % и т.д. не ломают URI).
    """
    user = quote_plus(MONGO_USER)
    password = quote_plus(MONGO_PASSWORD)
    return f"mongodb://{user}:{password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}"