import os

session_path = 'M:\Projects\Pycharm_projects\GPT_API_test\test'

os.makedirs(session_path, exist_ok=True)

session_name = 'my_telegram_session_1'

session_file_path = os.path.join(session_path, session_name)

print(f"Файл сессии будет сохранен по пути: {session_file_path}.session")

