# api_server.py
import base64
import hashlib
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
import uvicorn
from validation.nodes_settings import *
from config import API_HOST, API_PORT
# Корень проекта для импорта repositories, services, config и т.д.
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from services.workflow_service_v3 import (
    ExecuteWorkflowResult,
    LocalComfyUIClient,
    ProcessType,
)
from repositories.workflow_run_repository import (
    build_run_document,
    ensure_indexes,
    find_cached_image_by_request_hash,
    insert_run,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создание индексов MongoDB при старте приложения."""
    await ensure_indexes()
    yield


app = FastAPI(
    title="ComfyUI Workflow API",
    description="API для выполнения workflow ComfyUI",
    version="1.0.0",
    lifespan=lifespan,
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


def _request_hash(process_type: ProcessType, params: dict) -> str:
    """Детерминированный хэш запроса: одинаковые process_type + params → один и тот же hash (кэш)."""
    payload = {"process_type": process_type.value, "params": params}
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _result_to_image_bytes_from_b64(result_b64: str) -> bytes:
    """Преобразует base64-строку (из ExecuteWorkflowResult.image) в байты изображения."""
    if result_b64.startswith("data:image"):
        _, encoded = result_b64.split(",", 1)
        return base64.b64decode(encoded)
    return base64.b64decode(result_b64)


async def _save_workflow_run(
    result: ExecuteWorkflowResult,
    status: str = "success",
    error_message: Optional[str] = None,
    response_meta: Optional[dict] = None,
    request_hash: Optional[str] = None,
    response_image_base64: Optional[str] = None,
) -> None:
    """Пишет запись о запуске в MongoDB. Ошибки только логируются."""
    doc = build_run_document(
        client_id=result.client_id,
        prompt_id=result.prompt_id,
        process_type=result.process_type.value,
        params=result.params,
        processed_workflow=result.processed_workflow,
        status=status,
        error_message=error_message,
        response_meta=response_meta,
        request_hash=request_hash,
        response_image_base64=response_image_base64,
    )
    inserted_id = await insert_run(doc)
    if inserted_id:
        logger.debug("Workflow run saved: %s", inserted_id)


async def _run_workflow_and_return_image(
    process_type: ProcessType,
    params: BaseModel,
    timeout: int,
    service: LocalComfyUIClient,
) -> Response:
    """Выполняет workflow или отдаёт изображение из кэша при идентичном запросе."""
    params_dict = params.model_dump()
    req_hash = _request_hash(process_type, params_dict)

    cached_b64 = await find_cached_image_by_request_hash(req_hash)
    if cached_b64:
        image_bytes = _result_to_image_bytes_from_b64(cached_b64)
        filename = f"{process_type.value}.png"
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename={filename}"},
        )

    try:
        result: ExecuteWorkflowResult = await service.execute_workflow2(
            process_type=process_type,
            params=params_dict,
            timeout=timeout,
        )
        image_bytes = _result_to_image_bytes_from_b64(result.image)
        response_meta = {"content_type": "image/png", "size_bytes": len(image_bytes)}

        await _save_workflow_run(
            result,
            status="success",
            response_meta=response_meta,
            request_hash=req_hash,
            response_image_base64=result.image,
        )

        filename = f"{process_type.value}.png"
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename={filename}"},
        )
    except Exception as e:
        # Сохраняем запись об ошибке (минимальная запись: без prompt_id/processed_workflow при сбое до queue_prompt)
        try:
            err_doc = build_run_document(
                client_id=service.client_id,
                prompt_id="",
                process_type=process_type.value,
                params=params.model_dump(),
                processed_workflow={},
                status="error",
                error_message=str(e),
            )
            await insert_run(err_doc)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))


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
    uvicorn.run(app, host=API_HOST, port=API_PORT)