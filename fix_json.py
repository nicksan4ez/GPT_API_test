"""
Скрипт для исправления JSON файла result.json
"""

import json
import re

def fix_json_file(input_file, output_file):
    """Исправляет синтаксические ошибки в JSON файле"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"Размер файла: {len(content)} символов")

        # Исправляем возможные проблемы:
        # 1. Лишние запятые перед закрывающими скобками
        content = re.sub(r',(\s*[}\]])', r'\1', content)

        # 2. Двойные запятые
        content = re.sub(r',,+', ',', content)

        # 3. Запятые в конце объектов/массивов
        content = re.sub(r',(\s*}\s*)', r'\1', content)
        content = re.sub(r',(\s*]\s*)', r'\1', content)

        print("Попытка парсинга исправленного JSON...")

        # Проверяем валидность
        try:
            parsed = json.loads(content)
            print("✓ JSON успешно исправлен и валиден!")

            # Сохраняем исправленный файл
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed, f, ensure_ascii=False, indent=1)

            print(f"✓ Исправленный файл сохранен: {output_file}")
            return True

        except json.JSONDecodeError as e:
            print(f"✗ JSON все еще содержит ошибки: {e}")
            print(f"Строка {e.lineno}, позиция {e.colno}")

            # Попробуем найти и показать проблемное место
            lines = content.split('\n')
            if e.lineno <= len(lines):
                print(f"Проблемная строка: {lines[e.lineno-1]}")

            return False

    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")
        return False

if __name__ == "__main__":
    success = fix_json_file("result.json", "result_fixed.json")
    if success:
        print("JSON файл успешно исправлен!")
    else:
        print("Не удалось исправить JSON файл автоматически.")
