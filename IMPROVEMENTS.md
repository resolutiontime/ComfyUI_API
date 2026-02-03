# Анализ проекта ComfyUI API и предложения по доработке

## 1. Критические баги

### 1.1 Дубликат ветки `ProcessType.POSE` в `workflow_processor.py`
В `WorkflowFactory.process()` тип `ProcessType.POSE` обработан дважды: первый раз на строках 66–67, второй — на 76–78. Вторая ветка недостижима. Нужно удалить дубликат.

### 1.2 Неверный порядок аргументов в `execute_workflow`
В `workflow_service_v3.py` вызов:
```python
outputs = await self.wait_for_completion(prompt_id, timeout, progress_callback)
```
Сигнатура метода: `wait_for_completion(self, save_node_id, prompt_id, timeout, progress_callback)`.
Передаётся только 3 аргумента, `save_node_id` не передаётся — будет ошибка при вызове `execute_workflow` (не `execute_workflow2`).

### 1.3 Относительный путь `../workflows` в `execute_workflow2`
`WorkflowPathManager(base_dir='../workflows')` зависит от текущей рабочей директории. При запуске из корня проекта папка `workflows` не найдена. Нужно определять путь относительно корня проекта (например, `Path(__file__).resolve().parent / "workflows"`).

### 1.4 Отсутствует `import base64` в `api_methods.py`
В эндпоинтах используется `base64.b64decode`, но модуль не импортирован — при запросе изображения будет `NameError`.

### 1.5 `get_save_node_id` возвращает строку, а не Dict
В `node_mapping.py`: `return cls.MAPPINGS.get(process_type, {}).get('save_node_id', {})` — при отсутствии ключа возвращается `{}`, при наличии — строка (например `'244'`). Тип в аннотации `-> Dict` неверен; плюс в `_apply_params_to_workflow` ключ `save_node_id` попадает в маппинг и итерируется как нода (у него нет `node_id`/`input_name`). Нужно исключать служебные ключи из маппинга при применении параметров.

---

## 2. Архитектура и рефакторинг

### 2.1 Дублирование кода в API
Три эндпоинта `get_portrait_image`, `get_pose_image`, `get_pose_dt_image` почти идентичны (около 40 строк × 3). Предложение:
- Вынести общую функцию `result_to_image_bytes(result)` и единый обработчик `run_workflow_and_return_image(process_type: ProcessType, request: WorkflowRequest)`.
- Либо один эндпоинт `POST /api/v1/run/{process_type}/image` с `process_type: portrait | pose | pose_dt`.

### 2.2 Инициализация сервиса на каждый запрос
В каждом эндпоинте создаётся `LocalComfyUIClient()`. Лучше использовать зависимость FastAPI (dependency) с возможностью конфигурации host/port и при необходимости пулом/синглтоном.

### 2.3 Конфигурация
- Вынести host/port ComfyUI и базовый каталог workflows в переменные окружения или конфиг (например `config.py` или `.env`).
- В `WorkflowPathManager` и `LocalComfyUIClient` использовать этот конфиг вместо захардкоженных `../workflows` и `localhost:8000`.

### 2.4 Валидация и типы
- `WorkflowRequest.params` — `Optional[dict]` с дефолтным мутабельным словарём; лучше явная Pydantic-модель (например, наследование от `PortraitParams`/`PoseParams`) или `dict` без дефолта.
- Добавить аннотации возвращаемых типов у методов (например, `get_image_from_history` возвращает `Optional[Tuple[str, str]]`).

---

## 3. Качество кода

### 3.1 Отладочные выводы
Убрать или заменить на логгер: `print("www")` в `path_manager.get_path()`, `print(output_data['images'])`, `print("Sava_node_id", ...)`, `print(msg)` в WebSocket, `print('Завершено!!!')`, `print("Execution was served from cache")`.

### 3.2 Обработка исключений
В API при разборе base64 используется `except: print('Какой то другой формат')` — глотается исключение, при ошибке декодирования можно вернуть клиенту некорректные данные. Нужно логировать и при неверном формате возвращать 500 или 400 с сообщением.

### 3.3 Маппинг нод и служебные ключи
В `_apply_params_to_workflow` перебираются все ключи маппинга, включая `save_node_id`, у которого нет `node_id`/`input_name`. Нужно пропускать ключи, не являющиеся параметрами нод (например, не содержащие `node_id`), или хранить `save_node_id` отдельно от маппинга параметров.

---

## 4. Функциональность и документация

### 4.1 Тип `ProcessType.PORTRAIT_TO_POSE`
В `path_manager` есть путь для `PORTRAIT_TO_POSE`, но в `WorkflowFactory.process` и в API эндпоинтов он не обработан — при вызове будет `ValueError`. Либо добавить поддержку (маппинг, параметры, эндпоинт), либо явно не документировать до реализации.

### 4.2 README
Сейчас README не информативен. Имеет смысл описать: назначение проекта, требования (Python, ComfyUI), установку зависимостей, переменные окружения, примеры запуска API и вызова эндпоинтов (curl или Swagger).

### 4.3 Эндпоинт для PORTRAIT_DT
В API есть portrait, pose, pose_dt; для портретного детайлера (`PORTRAIT_DT`) отдельного эндпоинта нет — при необходимости добавить или документировать единый `run/{process_type}/image`.

---

## 5. Приоритеты внедрения

| Приоритет | Задача |
|-----------|--------|
| P0 | Исправить отсутствующий `import base64` в api_methods.py |
| P0 | Исправить порядок аргументов в `execute_workflow` или сигнатуру `wait_for_completion` |
| P0 | Исключить `save_node_id` из итерации в `_apply_params_to_workflow` (или убрать из маппинга при обходе) |
| P1 | Удалить дубликат ветки POSE в workflow_processor.py |
| P1 | Заменить жёсткий путь `../workflows` на путь относительно корня проекта |
| P1 | Рефакторинг API: общая функция конвертации result → image bytes и общий обработчик по process_type |
| P2 | Убрать print, перевести на logger; улучшить except в API |
| P2 | Конфиг (env/config) для host, port, base_dir |
| P2 | Обновить README с инструкциями и примерами |

---

## 6. Что уже внесено в код

- **workflow_processor.py**: удалён дубликат ветки `ProcessType.POSE`; в `_apply_params_to_workflow` добавлен пропуск ключа `save_node_id` и других записей без `node_id`, чтобы они не обрабатывались как ноды.
- **node_mapping.py**: тип возврата `get_save_node_id` исправлен (возвращается строка или None).
- **path_manager.py**: убран отладочный `print("www")`; в `__init__` добавлена поддержка `base_dir` типа `Path`.
- **workflow_service_v3.py**: сигнатура `wait_for_completion` изменена на `(prompt_id, timeout, progress_callback=None, save_node_id=None)`; в `execute_workflow2` путь к workflows задаётся относительно корня проекта (`Path(__file__).resolve().parent.parent / "workflows"`); отладочные `print` заменены на `logger.info`/`logger.debug`; при отсутствии изображения в выводе выбрасывается понятная ошибка.
- **api_methods.py**: добавлен `import base64`; добавлены `_result_to_image_bytes` и `_run_workflow_and_return_image`; эндпоинты portrait/pose/pose_dt переписаны на общий обработчик; `WorkflowRequest.params` сделан опциональным с методом `get_params()` для дефолтных значений.
