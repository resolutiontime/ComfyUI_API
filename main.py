# from services.workfloweditor_service_v2 import *
from services.workflow_service_v3 import *

def main():
    config = Config(
        # server_ip='46.0.234.168',
        server_ip='localhost',
        port='8000',
        timeout=30,
        max_retries=3,
        poll_interval=0.5,
        max_wait_time=300
    )

    process_name = ProcessType.PORTRAIT
    path_mngr = WorkflowPathManager()
    workflow = path_mngr.load_workflow(process_name)

    # Создаем параметры для портрета
    portrait_params = {
        "width": 896,
        "height": 1216,
        #         "cfg": 3,
        #         "steps": 20,
        "prompt": "beautiful portrait of a woman, yellow eyes",
        "seed": 45
    }

    # Обрабатываем workflow
    processed_workflow = WorkflowFactory.process(
        process_type=process_name,
        params=portrait_params,
        workflow_template=workflow
    )

    # Создаем клиент
    api_client = ComfyUIClient(config)

    # Отправляем промт
    prompt_id = api_client.post_prompt(processed_workflow)

    # Ждем завершения
    history_data = api_client.wait_for_completion(prompt_id)

    # Получаем имя файла изображения
    filename, subfolder = api_client.get_image_from_history(history_data)
    print(filename, subfolder)

    if filename:
        image = api_client.get_image(filename, subfolder)
        api_client.display_image(image)


def main2():
    client = LocalComfyUIClient()

    process_name = ProcessType.PORTRAIT
    path_mngr = WorkflowPathManager()
    workflow = path_mngr.load_workflow(process_name)

    # Создаем параметры
    params = {
        "width": 896,
        "height": 1216,
        #         "cfg": 3,
        # "steps": 15,
        "prompt": "open mouth",
        "seed": 45
    }

    # Обрабатываем workflow
    processed_workflow = WorkflowFactory.process(
        process_type=process_name,
        params=params,
        workflow_template=workflow
    )

    img = asyncio.run(client.execute_workflow(processed_workflow, 20))
    asyncio.run(client.display_image(img))

if __name__ == '__main__':
    main2()

