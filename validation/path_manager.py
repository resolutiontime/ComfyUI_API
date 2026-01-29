from validation.nodes_settings import *
from pathlib import Path
import json

class WorkflowPathManager:
    """Менеджер путей к файлам workflow"""

    # Базовые пути по умолчанию
    DEFAULT_PATHS = {
        ProcessType.PORTRAIT: "Generate_portrait_API.json",
        ProcessType.POSE: "Generate_pose_API.json",
    }

    def __init__(self, base_dir: str = "workflows", custom_paths: Dict[ProcessType, str] = None):
        self.base_dir = Path(base_dir)
        self.paths = self.DEFAULT_PATHS.copy()

        if custom_paths:
            self.paths.update(custom_paths)

    def get_path(self, process_type: ProcessType) -> Path:
        """Получить полный путь к файлу workflow"""
        filepath = self.paths.get(process_type)
        if not filepath:
            raise ValueError(f"No workflow path defined for {process_type}")

        # Если путь абсолютный - возвращаем как есть
        path = Path(filepath)
        if path.is_absolute():
            return path

        # Иначе ищем относительно base_dir
        print("www")
        return self.base_dir / path

    def load_workflow(self, process_type: ProcessType) -> Dict[str, Any]:
        """Загрузить workflow из файла"""
        filepath = self.get_path(process_type)

        if not filepath.exists():
            raise FileNotFoundError(f"Workflow file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_workflow(self, process_type: ProcessType, workflow: Dict[str, Any]) -> None:
        """Сохранить workflow в файл"""
        filepath = self.get_path(process_type)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)

    def register_path(self, process_type: ProcessType, filepath: str) -> None:
        """Зарегистрировать новый путь для типа процесса"""
        self.paths[process_type] = filepath


if __name__ == '__main__':
    print("It`s 'path_manager.py'")
    path_manager = WorkflowPathManager()
    print(path_manager.load_workflow(ProcessType.POSE))
    # print(path_manager.get_path(ProcessType.POSE))