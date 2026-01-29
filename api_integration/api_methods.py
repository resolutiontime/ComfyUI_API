# api_server.py
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Any, Optional
import uvicorn
import sys
import os

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем ваш сервис
from services.workflow_service_v3 import *

# Или, если используется другой класс, например:
# from workflow_controller import WorkflowController

app = FastAPI(
    title="ComfyUI Workflow API",
    description="API для выполнения workflow ComfyUI",
    version="1.0.0"
)

# Инициализация сервиса (можно вынести в зависимости)
service = LocalComfyUIClient()


class WorkflowRequest(BaseModel):
    """Модель запроса для выполнения workflow"""
    # workflow_path: str
    # output_dir: str
    # input_params: Optional[dict] = None
    # output_format: Optional[str] = "png"
    # save_output: Optional[bool] = True
    timeout: int = 20
    params: Optional[dict] = {
        "width": 896,
        "height": 1216,
        "cfg": 3,
        "steps": 18,
        "prompt": "open mouth",
        "seed": 46
    }


@app.post("/api/v1/get_portait")
async def execute_workflow(request: WorkflowRequest):
    """
    params default:
    "width": 896,
    "height": 1216,
    "cfg": 3,
    "steps": 15,
    "prompt": "open mouth",
    "seed": 46
    """
    try:
        # Вызов вашего существующего сервиса
        result = await service.execute_workflow2(
            params=request.params,
            timeout=request.timeout
        )

        return {
            "status": "success",
            "message": "Workflow выполнен успешно",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/get_portait/image",
          responses={
              200: {
                  "content": {"image/png": {}},
                  "description": "Возвращает PNG изображение"
              }
          })
async def get_portrait_image(request: WorkflowRequest):
    """Возвращает изображение портрета (отображается прямо в Swagger UI)"""
    try:
        result = await service.execute_workflow2(
            params=request.params,
            timeout=request.timeout
        )

        # Определяем тип результата
        if isinstance(result, str):
            # Вариант 1: строка начинается с data:image (base64 с префиксом)
            if result.startswith('data:image'):
                # Извлекаем base64 часть после запятой
                header, encoded = result.split(',', 1)
                image_bytes = base64.b64decode(encoded)

            # Вариант 2: чистая base64 строка (без префикса)
            elif len(result) > 100 and ' ' not in result:  # Простая эвристика
                try:
                    image_bytes = base64.b64decode(result)
                except:
                    print('Какой то другой формат')

            # Вариант 3: путь к файлу
            elif os.path.exists(result):
                with open(result, 'rb') as f:
                    image_bytes = f.read()

            # Вариант 4: прочая строка
            else:
                # Пробуем интерпретировать как обычную строку байтов
                image_bytes = result.encode('utf-8')

        elif isinstance(result, bytes):
            # Уже байты
            image_bytes = result

        else:
            # Неизвестный формат
            raise ValueError(f"Неизвестный формат результата: {type(result)}")

        # Возвращаем изображение
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={"Content-Disposition": "inline; filename=portrait.png"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {"status": "healthy", "service": "ComfyUI Workflow API"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)