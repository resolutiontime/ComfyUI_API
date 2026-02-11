# api_server.py
import base64
import os
import sys
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
import uvicorn
from validation.nodes_settings import *
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


class PortraitRequest(BaseModel):
    """Запрос на генерацию портрета."""
    timeout: int = Field(20, description="Таймаут выполнения workflow в секундах")
    params: PortraitParams = Field(  # type: ignore[name-defined]
        default_factory=PortraitParams,
        description="Параметры генерации портрета (дефолты см. в PortraitParams)",
    )


class PoseRequest(BaseModel):
    """Запрос на генерацию позы."""
    timeout: int = Field(20, description="Таймаут выполнения workflow в секундах")
    params: PoseParams = Field(  # type: ignore[name-defined]
        default_factory=PoseParams,
        description="Параметры генерации позы (дефолты см. в PoseParams)",
    )


class PoseDetailRequest(BaseModel):
    """Запрос на генерацию позы с детайлером."""
    timeout: int = Field(20, description="Таймаут выполнения workflow в секундах")
    params: PoseParams = Field(  # type: ignore[name-defined]
        default_factory=PoseParams,
        description="Параметры генерации позы для детайлера (дефолты см. в PoseParams)",
    )


# class WorkflowRequest():
#     """Модель запроса для выполнения workflow"""
#     timeout: int = 20
#     params: PortraitParams().model_dump()
#
#     # process_type: ProcessType
#     # def get_params(self) -> dict:
#     #     if self.params is not None:
#     #         return self.params
#     #     return {
#     #         "width": 896,
#     #         "height": 1216,
#     #         "cfg": 3,
#     #         "steps": 18,
#     #         "prompt": "open mouth",
#     #         "seed": 46,
#     #     }


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
    params: BaseModel,
    timeout: int,
    service: LocalComfyUIClient,
) -> Response:
    """Общий помощник: выполняет workflow и возвращает PNG-изображение."""
    print("CLIENT ID: ", service.client_id)

    result = await service.execute_workflow2(
        process_type=process_type,
        params=params.model_dump(),
        timeout=timeout,
    )
    image_bytes = _result_to_image_bytes(result)
    filename = f"{process_type.value}.png"
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@app.post(
    "/api/v1/get_portait/image",
    responses={200: {"content": {"image/png": {}}, "description": "Возвращает PNG изображение"}},
)
async def get_portrait_image(request: PortraitRequest):
    """Возвращает изображение портрета (отображается в Swagger UI)."""
    service = LocalComfyUIClient()
    try:
        return await _run_workflow_and_return_image(
            ProcessType.PORTRAIT,
            params=request.params,
            timeout=request.timeout,
            service=service,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/v1/get_pose/image",
    responses={200: {"content": {"image/png": {}}, "description": "Возвращает PNG изображение"}},
)
async def get_pose_image(request: PoseRequest):
    """Возвращает изображение позы (отображается в Swagger UI)."""
    service = LocalComfyUIClient()
    try:
        return await _run_workflow_and_return_image(
            ProcessType.POSE,
            params=request.params,
            timeout=request.timeout,
            service=service,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/v1/get_pose_dt/image",
    responses={200: {"content": {"image/png": {}}, "description": "Возвращает PNG изображение"}},
)
async def get_pose_dt_image(request: PoseDetailRequest):
    """Возвращает изображение позы с детайлером (отображается в Swagger UI)."""
    service = LocalComfyUIClient()
    try:
        return await _run_workflow_and_return_image(
            ProcessType.POSE_DT,
            params=request.params,
            timeout=request.timeout,
            service=service,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {"status": "healthy", "service": "ComfyUI Workflow API"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)