from validation.node_mapping import *
from validation.path_manager import *
import logging

logger = logging.getLogger(__name__)


class WorkflowProcessor:
    def __init__(self, base_workflow: Dict[str, Any]):
        self.base_workflow = base_workflow
        self.node_mapping = NodeMapping()

    def process(self, params, process_type: ProcessType) -> Dict[str, Any]:
        """Обработка workflow: применение параметров и Lora настроек"""
        workflow = self._deep_copy_workflow()
        mapping = self.node_mapping.get_mapping(process_type)
        
        # Применяем базовые параметры
        workflow = self._apply_params_to_workflow(workflow, params, mapping)
        
        # Применяем Lora настройки
        workflow = self._apply_lora_settings(workflow, params, process_type)
        
        return workflow

    def _apply_params_to_workflow(
            self,
            workflow: Dict[str, Any],
            params: BaseModel,
            mapping: Dict
    ) -> Dict[str, Any]:
        """Применение параметров к workflow через маппинг"""

        param_dict = params.model_dump()

        for param_name, node_info in mapping.items():
            if param_name == "save_node_id" or "node_id" not in node_info:
                continue
            if param_name in param_dict and param_dict[param_name] is not None:
                node_id = str(node_info["node_id"])
                input_name = node_info["input_name"]

                # Находим ноду в workflow
                if node_id in workflow:
                    # Устанавливаем значение в inputs ноды
                    if "inputs" not in workflow[node_id]:
                        workflow[node_id]["inputs"] = {}

                    workflow[node_id]["inputs"][input_name] = param_dict[param_name]
                else:
                    print(f"Warning: Node {node_id} not found in workflow")

        return workflow

    def _apply_lora_settings(
            self,
            workflow: Dict[str, Any],
            params: BaseModel,
            process_type: ProcessType
    ) -> Dict[str, Any]:
        """
        Применение Lora настроек к workflow.
        
        Заменяет все lora_X слоты в ноде Power Lora Loader на переданные настройки.
        """
        # Получаем lora_settings из params
        lora_settings: Optional[LoraSettings] = getattr(params, 'lora_settings', None)
        
        if lora_settings is None:
            return workflow
        
        # Получаем список Lora слотов (пресет + кастомные)
        lora_slots: List[LoraSlot] = lora_settings.get_all_lora_slots()
        
        if not lora_slots:
            # Если список пуст и preset=NONE — выключаем все Lora в ноде
            if lora_settings.preset == LoraPreset.NONE:
                return self._disable_all_lora(workflow, process_type)
            return workflow
        
        # Получаем node_id ноды Power Lora Loader
        lora_node_id = self.node_mapping.get_lora_node_id(process_type)
        if not lora_node_id:
            logger.warning(f"Lora node_id not found for process_type: {process_type}")
            return workflow
        
        if lora_node_id not in workflow:
            logger.warning(f"Lora node {lora_node_id} not found in workflow")
            return workflow
        
        lora_node_inputs = workflow[lora_node_id]["inputs"]
        
        # Сначала выключаем все существующие Lora слоты
        for key in list(lora_node_inputs.keys()):
            if key.startswith("lora_") and isinstance(lora_node_inputs[key], dict):
                lora_node_inputs[key]["on"] = False
        
        # Применяем переданные Lora слоты
        for i, lora_slot in enumerate(lora_slots, start=1):
            slot_key = f"lora_{i}"
            lora_node_inputs[slot_key] = {
                "on": lora_slot.on,
                "lora": lora_slot.lora,
                "strength": lora_slot.strength
            }
            logger.debug(f"Applied Lora slot {slot_key}: {lora_slot.lora} (strength={lora_slot.strength}, on={lora_slot.on})")
        
        return workflow
    
    def _disable_all_lora(
            self,
            workflow: Dict[str, Any],
            process_type: ProcessType
    ) -> Dict[str, Any]:
        """Выключает все Lora в ноде Power Lora Loader"""
        lora_node_id = self.node_mapping.get_lora_node_id(process_type)
        if not lora_node_id or lora_node_id not in workflow:
            return workflow
        
        lora_node_inputs = workflow[lora_node_id]["inputs"]
        
        for key in list(lora_node_inputs.keys()):
            if key.startswith("lora_") and isinstance(lora_node_inputs[key], dict):
                lora_node_inputs[key]["on"] = False
        
        logger.debug(f"Disabled all Lora in node {lora_node_id}")
        return workflow

    def _deep_copy_workflow(self) -> Dict[str, Any]:
        """Создание глубокой копии workflow"""
        import json
        return json.loads(json.dumps(self.base_workflow))


class WorkflowFactory:
    @staticmethod
    def create_processor(workflow_template: Dict[str, Any]) -> WorkflowProcessor:
        return WorkflowProcessor(workflow_template)

    @staticmethod
    def process(
            process_type: ProcessType,
            params: Dict[str, Any],
            workflow_template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Упрощенный метод для обработки workflow"""

        processor = WorkflowProcessor(workflow_template)

        # Создаем соответствующую модель параметров
        if process_type == ProcessType.PORTRAIT:
            validated_params = PortraitParams(**params)
            return processor.process(validated_params, process_type)
        elif process_type == ProcessType.POSE:
            validated_params = PoseParams(**params)
            return processor.process(validated_params, process_type)
        elif process_type == ProcessType.POSE_DT:
            validated_params = PoseParams(**params)
            return processor.process(validated_params, process_type)
        elif process_type == ProcessType.PORTRAIT_DT:
            validated_params = PortraitParams(**params)
            return processor.process(validated_params, process_type)
        else:
            raise ValueError(f"Unknown process type: {process_type}")


if __name__ == '__main__':
    print("It`s 'workflow_manager.py'")
    process = ProcessType.POSE_DT

    path_mngr = WorkflowPathManager(base_dir='../workflows')
    workflow = path_mngr.load_workflow(process)


    # Создаем параметры для портрета
    portrait_params = {
        "width": 896,
        "height": 1216,
        "cfg": 4,
        #         "steps": 20,
        "prompt": "beautiful portrait of a woman",
        "seed": 42
    }

    # Обрабатываем workflow
    processed_workflow = WorkflowFactory.process(
        process_type=process,
        params=portrait_params,
        workflow_template=workflow
    )

