"""
Репозиторий для сохранения записей о запусках workflow в MongoDB.
Ошибки записи логируются и не пробрасываются, чтобы не ломать ответ API.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_DB_NAME, get_mongo_uri

logger = logging.getLogger(__name__)

COLLECTION_NAME = "workflow_runs"


def _get_client() -> AsyncIOMotorClient:
    """Ленивая инициализация клиента MongoDB (один на процесс)."""
    if not hasattr(_get_client, "_client"):
        _get_client._client = AsyncIOMotorClient(get_mongo_uri())
    return _get_client._client


def _get_collection():
    return _get_client()[MONGO_DB_NAME][COLLECTION_NAME]


async def ensure_indexes() -> None:
    """Создаёт индексы для частых запросов (идемпотентно)."""
    try:
        coll = _get_collection()
        await coll.create_index("client_id")
        await coll.create_index("prompt_id")
        await coll.create_index("request_hash")
        await coll.create_index([("created_at", -1)])
        await coll.create_index([("client_id", "created_at")])
    except Exception as e:
        logger.warning("Could not ensure workflow_runs indexes: %s", e)


def build_run_document(
    *,
    client_id: str,
    prompt_id: str,
    process_type: str,
    params: Dict[str, Any],
    processed_workflow: Dict[str, Any],
    status: str,
    error_message: str | None = None,
    response_meta: Dict[str, Any] | None = None,
    request_hash: str | None = None,
    response_image_base64: str | None = None,
) -> Dict[str, Any]:
    """Собирает документ для вставки в коллекцию workflow_runs."""
    doc: Dict[str, Any] = {
        "client_id": client_id,
        "prompt_id": prompt_id,
        "process_type": process_type,
        "params": params,
        "processed_workflow": processed_workflow,
        "status": status,
        "created_at": datetime.now(timezone.utc),
    }
    if error_message is not None:
        doc["error_message"] = error_message
    if response_meta:
        doc["response_meta"] = response_meta
    if request_hash is not None:
        doc["request_hash"] = request_hash
    if response_image_base64 is not None:
        doc["response_image_base64"] = response_image_base64
    return doc


async def find_cached_image_by_request_hash(request_hash: str) -> str | None:
    """
    Возвращает base64 изображения из последнего успешного run с данным request_hash.
    Если кэша нет — None. Используется для повторных идентичных запросов без вызова ComfyUI.
    """
    try:
        coll = _get_collection()
        doc = await coll.find_one(
            {"request_hash": request_hash, "status": "success", "response_image_base64": {"$exists": True, "$ne": ""}},
            projection={"response_image_base64": 1},
            sort=[("created_at", -1)],
        )
        if doc and doc.get("response_image_base64"):
            return doc["response_image_base64"]
        return None
    except Exception as e:
        logger.warning("find_cached_image_by_request_hash failed: %s", e)
        return None


async def insert_run(doc: Dict[str, Any]) -> str | None:
    """
    Вставляет запись о запуске в MongoDB.
    Возвращает inserted_id или None при ошибке. Ошибки только логируются.
    """
    try:
        coll = _get_collection()
        result = await coll.insert_one(doc)
        return str(result.inserted_id)
    except Exception as e:
        logger.exception("Failed to insert workflow run: %s", e)
        return None
