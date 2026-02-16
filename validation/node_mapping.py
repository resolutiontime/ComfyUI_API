from validation.nodes_settings import *
import copy
from typing import List


class NodeMapping:
    """Конфигурация маппинга параметров на ноды ComfyUI"""

    # Маппинг для каждого типа процесса
    MAPPINGS = {
        ProcessType.POSE: {
            "width": {"node_id": 194, "input_name": "value"},
            "height": {"node_id": 195, "input_name": "value"},
            "cfg": {"node_id": 196, "input_name": "value"},
            "steps": {"node_id": 197, "input_name": "value"},
            "seed": {"node_id": 198, "input_name": "seed"},
            "sampler": {"node_id": 240, "input_name": "sampler_name"},
            "scheduler": {"node_id": 241, "input_name": "choice"},
            "prompt": {"node_id": 193, "input_name": "text"},
            "negative_prompt": {"node_id": 199, "input_name": "text"},

        },
        ProcessType.PORTRAIT: {
            "width": {"node_id": 159, "input_name": "value"},
            "height": {"node_id": 160, "input_name": "value"},
            "cfg": {"node_id": 161, "input_name": "value"},
            "steps": {"node_id": 162, "input_name": "value"},
            "seed": {"node_id": 163, "input_name": "seed"},
            "sampler": {"node_id": 238, "input_name": "sampler_name"},
            "scheduler": {"node_id": 239, "input_name": "choice"},
            "prompt": {"node_id": 164, "input_name": "text"},
            "negative_prompt": {"node_id": 165, "input_name": "text"},
        }}

    MAPPINGS[ProcessType.POSE_DT] = copy.deepcopy(MAPPINGS[ProcessType.POSE])
    MAPPINGS[ProcessType.PORTRAIT_DT] = copy.deepcopy(MAPPINGS[ProcessType.PORTRAIT])

    MAPPINGS[ProcessType.POSE].update({'save_node_id':'244'})
    MAPPINGS[ProcessType.POSE_DT].update({'save_node_id':'245'})
    MAPPINGS[ProcessType.PORTRAIT].update({'save_node_id':'230'})
    MAPPINGS[ProcessType.PORTRAIT_DT].update({'save_node_id':'243'})

    # Маппинг Lora нод для каждого ProcessType
    # node_id ноды "Power Lora Loader (rgthree)" в workflow
    LORA_NODE_MAPPING: Dict[ProcessType, str] = {
        ProcessType.PORTRAIT: "186",
        ProcessType.PORTRAIT_DT: "186",
        ProcessType.POSE: "205",
        ProcessType.POSE_DT: "205",
    }

    @classmethod
    def get_mapping(cls, process_type: ProcessType) -> Dict:
        return cls.MAPPINGS.get(process_type, {})

    @classmethod
    def get_save_node_id(cls, process_type: ProcessType):
        return cls.MAPPINGS.get(process_type, {}).get('save_node_id')

    @classmethod
    def get_lora_node_id(cls, process_type: ProcessType) -> Optional[str]:
        """Возвращает node_id ноды Power Lora Loader для данного ProcessType"""
        return cls.LORA_NODE_MAPPING.get(process_type)


if __name__ == '__main__':
    obj = NodeMapping()

    print(obj.get_mapping(ProcessType.POSE))
