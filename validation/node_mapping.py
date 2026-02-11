from validation.nodes_settings import *
import copy


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


    @classmethod
    def get_mapping(cls, process_type: ProcessType) -> Dict:
        return cls.MAPPINGS.get(process_type, {})

    @classmethod
    def get_save_node_id(cls, process_type: ProcessType):
        return cls.MAPPINGS.get(process_type, {}).get('save_node_id')


if __name__ == '__main__':
    obj = NodeMapping()

    print(obj.get_mapping(ProcessType.POSE))
