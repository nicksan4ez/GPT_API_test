"""
Улучшенный скрипт для исправления и анализа JSON файла
"""

import json
import re

def try_fix_json(content):
    """Пытается исправить распространенные ошибки JSON"""
    # Удаляем лишние запятые перед закрывающими скобками
    content = re.sub(r',(\s*[}\]])', r'\1', content)

    # Удаляем двойные запятые
    content = re.sub(r',,+', ',', content)

    # Исправляем запятые в конце
    content = re.sub(r',(\s*})', r'\1', content)
    content = re.sub(r',(\s*])', r'\1', content)

    return content

def process_telegram_export():
    """Обрабатывает экспорт Telegram и запускает анализ"""
    try:
        print("Читаем файл result.json...")
        with open('result.json', 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"Размер файла: {len(content)} символов")

        # Пытаемся исправить JSON
        fixed_content = try_fix_json(content)

        # Пытаемся парсить
        try:
            data = json.loads(fixed_content)
            print("✓ JSON успешно загружен!")
        except json.JSONDecodeError as e:
            print(f"Ошибка JSON на строке {e.lineno}: {e.msg}")

            # Пытаемся найти и исправить конкретную ошибку
            lines = fixed_content.split('\n')
            if e.lineno <= len(lines):
                problematic_line = lines[e.lineno - 1]
                print(f"Проблемная строка: {problematic_line.strip()}")

                # Если это проблема с запятой в конце
                if problematic_line.strip() == '},':
                    lines[e.lineno - 1] = problematic_line.replace('},', '}')
                    fixed_content = '\n'.join(lines)
                    data = json.loads(fixed_content)
                    print("✓ Исправлено и загружено!")
                else:
                    raise e

        # Сохраняем исправленный файл
        with open('result_fixed.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✓ Исправленный файл сохранен как result_fixed.json")

        # Анализируем структуру
        print(f"\nИнформация о канале:")
        print(f"Название: {data.get('name', 'N/A')}")
        print(f"Тип: {data.get('type', 'N/A')}")
        print(f"ID: {data.get('id', 'N/A')}")

        messages = data.get('messages', [])
        print(f"Всего записей: {len(messages)}")

        # Анализируем типы сообщений
        types = {}
        text_messages = 0
        for msg in messages:
            msg_type = msg.get('type', 'unknown')
            types[msg_type] = types.get(msg_type, 0) + 1

            # Считаем сообщения с текстом
            if msg_type == 'message' and msg.get('text'):
                text_messages += 1

        print(f"Типы записей: {types}")
        print(f"Сообщений с текстом: {text_messages}")

        return True

    except Exception as e:
        print(f"Ошибка при обработке: {e}")
        return False

if __name__ == "__main__":
    success = process_telegram_export()
    if success:
        print("\n✓ Обработка завершена успешно!")
        print("Теперь можно запустить анализатор с файлом result_fixed.json")
    else:
        print("\n✗ Ошибка при обработке файла")
