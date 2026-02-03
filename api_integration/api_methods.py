# api_server.py
import base64
import os
import sys
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import uvicorn

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.workflow_service_v3 import LocalComfyUIClient, ProcessType

# Или, если используется другой класс, например:
# from workflow_controller import WorkflowController

app = FastAPI(
    title="ComfyUI Workflow API",
    description="API для выполнения workflow ComfyUI",
    version="1.0.0"
)


class WorkflowRequest(BaseModel):
    """Модель запроса для выполнения workflow"""
    timeout: int = 20
    params: Optional[dict] = None

    def get_params(self) -> dict:
        if self.params is not None:
            return self.params
        return {
            "width": 896,
            "height": 1216,
            "cfg": 3,
            "steps": 18,
            "prompt": "open mouth",
            "seed": 46,
        }


def _result_to_image_bytes(result: Any) -> bytes:
    """Преобразует результат execute_workflow2 (str base64 или bytes) в байты изображения."""
    if isinstance(result, bytes):
        return result
    if isinstance(result, str):
        if result.startswith("data:image"):
            _, encoded = result.split(",", 1)
            return base64.b64decode(encoded)
        if len(result) > 100 and " " not in result:
            return base64.b64decode(result)
        if os.path.exists(result):
            with open(result, "rb") as f:
                return f.read()
        raise ValueError("Не удалось интерпретировать результат как изображение")
    raise ValueError(f"Неизвестный формат результата: {type(result)}")


async def _run_workflow_and_return_image(
    process_type: ProcessType,
    request: WorkflowRequest,
    service: LocalComfyUIClient,
) -> Response:
    result = await service.execute_workflow2(
        process_type=process_type,
        params=request.get_params(),
        timeout=request.timeout,
    )
    image_bytes = _result_to_image_bytes(result)
    filename = f"{process_type.value}.png"
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )

#
# @app.post("/api/v1/get_portait")
# async def execute_workflow(request: WorkflowRequest):
#     """
#     params default:
#     "width": 896,
#     "height": 1216,
#     "cfg": 3,
#     "steps": 15,
#     "prompt": "open mouth",
#     "seed": 46
#     """
#     try:
#         # Вызов вашего существующего сервиса
#         result = await service.execute_workflow3(
#             params=request.params,
#             timeout=request.timeout
#         )
#
#         return {
#             "status": "success",
#             "message": "Workflow выполнен успешно",
#             "data": result
#         }
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/get_portait/image",
          responses={200: {"content": {"image/png": {}}, "description": "Возвращает PNG изображение"}})
async def get_portrait_image(request: WorkflowRequest):
    """Возвращает изображение портрета (отображается в Swagger UI)."""
    service = LocalComfyUIClient()
    try:
        return await _run_workflow_and_return_image(ProcessType.PORTRAIT, request, service)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/get_pose/image",
          responses={200: {"content": {"image/png": {}}, "description": "Возвращает PNG изображение"}})
async def get_pose_image(request: WorkflowRequest):
    """Возвращает изображение позы (отображается в Swagger UI)."""
    service = LocalComfyUIClient()
    try:
        return await _run_workflow_and_return_image(ProcessType.POSE, request, service)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/get_pose_dt/image",
          responses={200: {"content": {"image/png": {}}, "description": "Возвращает PNG изображение"}})
async def get_pose_dt_image(request: WorkflowRequest):
    """Возвращает изображение позы с детайлером (отображается в Swagger UI)."""
    service = LocalComfyUIClient()
    try:
        return await _run_workflow_and_return_image(ProcessType.POSE_DT, request, service)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {"status": "healthy", "service": "ComfyUI Workflow API"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)