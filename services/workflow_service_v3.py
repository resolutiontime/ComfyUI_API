import aiohttp
import asyncio
import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import base64
from validation.workflow_processor import *
from config import COMFYUI_HOST, COMFYUI_PORT

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalComfyUIClient:
    """Клиент для локального ComfyUI сервера"""

    def __init__(
            self,
            host: str = COMFYUI_HOST,
            port: int = COMFYUI_PORT,
            client_id: str = None
    ):
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}/ws"
        self.client_id = client_id or str(uuid.uuid4())
        self.node_mapping = NodeMapping()

    async def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Отправить промпт в очередь выполнения"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.base_url}/prompt",
                    json={"prompt": workflow}
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Failed to queue prompt: {text}")
                data = await resp.json()
                return data['prompt_id']

    async def get_history(self, prompt_id: str) -> Optional[Dict]:
        """Получить историю выполнения промпта"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"{self.base_url}/history/{prompt_id}"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    async def get_image(self, filename: str, subfolder: str = "", type: str = "output") -> bytes:
        """Получить изображение с сервера"""
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": type
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"{self.base_url}/view",
                    params=params
            ) as resp:
                if resp.status == 200:
                    return await resp.read()
                raise RuntimeError(f"Failed to get image: {resp.status}")

    async def display_image(self, image: Image.Image) -> None:
        """Отображает изображение"""
        image = Image.open(BytesIO(image))
        plt.figure(figsize=(10, 10))
        plt.imshow(image)
        plt.axis('off')
        plt.tight_layout()
        plt.show()

    async def get_image_base64(self, image: bytes) -> str:
        """Конвертирует изображение в base64 для передачи по сети"""
        # Если image уже bytes (например, из ComfyUI)
        if isinstance(image, bytes):
            img = Image.open(BytesIO(image))
        else:
            img = image

        # Конвертируем в base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return img_str

    async def get_image_from_history(self, history_data: Dict[str, Any]) -> Optional[str]:
        """Извлекает имя файла изображения из данных истории"""
        try:
            # Более гибкий поиск изображения в выводе
            for output_data in history_data.values():
                if 'images' in output_data and output_data['images'] and output_data['images'][0]['subfolder'] != '':
                    return output_data['images'][0]['filename'], output_data['images'][0]['subfolder']

            logger.warning("В выводе не найдено изображений")
            return None, None

        except KeyError as e:
            logger.error(f"Не удалось извлечь изображение: отсутствует ключ {e}")
            return None, None

    async def upload_image(self, image_data: bytes, filename: str = "upload.png") -> str:
        """Загрузить изображение на сервер"""
        data = aiohttp.FormData()
        data.add_field(
            'image',
            image_data,
            filename=filename,
            content_type='image/png'
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.base_url}/upload/image",
                    data=data
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get('name', filename)
                raise RuntimeError(f"Failed to upload image: {resp.status}")

    async def wait_for_completion(
            self,
            prompt_id: str,
            timeout: float = 300.0,
            progress_callback=None,
            save_node_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ожидать завершения выполнения через WebSocket"""
        ws_url = f"{self.ws_url}?clientId={self.client_id}"
        outputs = {}

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                start = asyncio.get_event_loop().time()

                async for msg in ws:
                    if asyncio.get_event_loop().time() - start > timeout:
                        raise TimeoutError("Job timed out")

                    if msg.type != aiohttp.WSMsgType.TEXT:
                        continue

                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        continue

                    # Проверяем, относится ли сообщение к нашему промпту
                    if data.get("data", {}).get("prompt_id") != prompt_id:
                        continue

                    msg_type = data.get("type")
                    msg_data = data.get("data", {})

                    if msg_type == "progress":
                        current = msg_data.get("value", 0)
                        total = msg_data.get("max", 1)

                        if progress_callback:
                            progress_callback(current, total)
                        else:
                            logger.debug("Progress: %s/%s", current, total)

                    elif msg_type == "progress_state":
                        if save_node_id and (msg_data.get('prompt_id') == prompt_id) and (msg_data.get('nodes', {}).get(save_node_id, {}).get('state') == 'finished'):
                            logger.info("Workflow node %s finished", save_node_id)
                            # Дополнительно получаем полную историю
                            history = await self.get_history(prompt_id)
                            if history and prompt_id in history:
                                outputs.update(history[prompt_id].get("outputs", {}))
                            return outputs

                    elif msg_type == "executed":
                        if output := msg_data.get("output"):
                            outputs[msg_data["node"]] = output

                    elif msg_type == "execution_success":
                        # Дополнительно получаем полную историю
                        history = await self.get_history(prompt_id)
                        if history and prompt_id in history:
                            outputs.update(history[prompt_id].get("outputs", {}))
                        return outputs

                    elif msg_type == "execution_error":
                        error_msg = msg_data.get("exception_message", "Unknown error")
                        raise RuntimeError(f"Execution failed: {error_msg}")

                    elif msg_type == "execution_cached":
                        logger.info("Execution was served from cache")
                        history = await self.get_history(prompt_id)
                        if history and prompt_id in history:
                            outputs.update(history[prompt_id].get("outputs", {}))
                        return outputs

        return outputs

    async def execute_workflow(
            self,
            workflow: Dict[str, Any],
            timeout: float = 300.0,
            progress_callback=None
    ) -> Dict[str, Any]:
        """Выполнить workflow и дождаться результата"""
        # Отправляем промпт
        prompt_id = await self.queue_prompt(workflow)

        # Ожидаем завершения (save_node_id не известен для произвольного workflow)
        outputs = await self.wait_for_completion(
            prompt_id,
            timeout,
            progress_callback,
            save_node_id=None,
        )

        filename, subfolder = await self.get_image_from_history(outputs)
        img = await self.get_image(filename, subfolder)

        return img


    async def execute_workflow2(
            self,
            process_type: ProcessType,
            timeout: float = 300.0,
            params: dict = None,

    ) -> Dict[str, Any]:

        process_name = process_type
        base_dir = Path(__file__).resolve().parent.parent / "workflows"
        path_mngr = WorkflowPathManager(base_dir=base_dir)
        workflow = path_mngr.load_workflow(process_name)

        save_node_id = self.node_mapping.get_save_node_id(process_name)
        logger.debug("save_node_id=%s", save_node_id)
        # Обрабатываем workflow
        processed_workflow = WorkflowFactory.process(
            process_type=process_name,
            params=params,
            workflow_template=workflow
        )

        # Отправляем промпт
        prompt_id = await self.queue_prompt(processed_workflow)

        # Ожидаем завершения
        outputs = await self.wait_for_completion(
            prompt_id,
            timeout,
            progress_callback=None,
            save_node_id=save_node_id,
        )

        filename, subfolder = await self.get_image_from_history(outputs)
        if filename is None:
            raise RuntimeError("В выводе workflow не найдено изображения")
        img = await self.get_image(filename, subfolder or "")

        return await self.get_image_base64(img)


if __name__ == '__main__':
    client = LocalComfyUIClient()

    # process = ProcessType.PORTRAIT
    # path_mngr = WorkflowPathManager(base_dir='../workflows')
    # workflow = path_mngr.load_workflow(process)
    #
    # img = asyncio.run(client.execute_workflow(workflow, 20))
    # asyncio.run(client.display_image(img))

    # Создаем параметры
    params = {
        "width": 896,
        "height": 1216,
        # "cfg": 3,
        # "steps": 15,
        "prompt": "open mouth",
        "seed": 47
    }

    asyncio.run(client.execute_workflow2(ProcessType.PORTRAIT_DT, params=params, timeout=15))
