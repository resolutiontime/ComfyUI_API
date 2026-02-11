"""
Глобальные настройки сервиса.

Здесь задаются хосты и порты для:
- FastAPI / uvicorn API
- локального ComfyUI сервера
"""

# Настройки HTTP API (FastAPI / uvicorn)
API_HOST: str = "0.0.0.0"
API_PORT: int = 8001

# Настройки локального ComfyUI сервера
COMFYUI_HOST: str = "localhost"
COMFYUI_PORT: int = 8000

