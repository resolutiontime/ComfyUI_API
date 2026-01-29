from validation.nodes_settings import *


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

    @classmethod
    def get_mapping(cls, process_type: ProcessType) -> Dict:
        return cls.MAPPINGS.get(process_type, {})