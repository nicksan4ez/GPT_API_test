"""
Устойчивый анализатор для экспорта Telegram с обработкой ошибок JSON
"""

import json
import re
from typing import List, Dict, Any
import os

class RobustTelegramAnalyzer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.messages = []
        self.channel_info = {}

    def try_load_json(self) -> bool:
        """Пытается загрузить JSON с различными методами исправления"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"Размер файла: {len(content)} символов")

            # Метод 1: Стандартная загрузка
            try:
                data = json.loads(content)
                self._extract_data(data)
                print("✓ JSON загружен стандартным способом")
                return True
            except json.JSONDecodeError as e:
                print(f"Ошибка JSON: {e}")
                print(f"Строка {e.lineno}, позиция {e.colno}")

            # Метод 2: Исправление распространенных ошибок
            print("Пытаемся исправить JSON...")
            fixed_content = self._fix_common_json_errors(content)

            try:
                data = json.loads(fixed_content)
                self._extract_data(data)
                print("✓ JSON загружен после исправления")
                return True
            except json.JSONDecodeError as e:
                print(f"JSON все еще содержит ошибки: {e}")

            # Метод 3: Частичная загрузка через регулярные выражения
            print("Пытаемся извлечь данные частично...")
            return self._extract_partial_data(content)

        except Exception as e:
            print(f"Критическая ошибка при загрузке файла: {e}")
            return False

    def _fix_common_json_errors(self, content: str) -> str:
        """Исправляет распространенные ошибки JSON"""
        # Удаляем лишние запятые
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        content = re.sub(r',,+', ',', content)

        # Исправляем незакрытые кавычки в тексте
        content = re.sub(r'(?<!\\)"(?=\s*\n)', r'\\"', content)

        # Исправляем проблемы с экранированием
        content = content.replace('\\"', '"')
        content = content.replace('\\\\', '\\')

        return content

    def _extract_partial_data(self, content: str) -> bool:
        """Извлекает данные частично, если JSON поврежден"""
        try:
            # Извлекаем основную информацию о канале
            name_match = re.search(r'"name":\s*"([^"]+)"', content)
            if name_match:
                self.channel_info['name'] = name_match.group(1)

            type_match = re.search(r'"type":\s*"([^"]+)"', content)
            if type_match:
                self.channel_info['type'] = type_match.group(1)

            id_match = re.search(r'"id":\s*(\d+)', content)
            if id_match:
                self.channel_info['id'] = int(id_match.group(1))

            # Извлекаем сообщения через регулярные выражения
            message_pattern = r'\{\s*"id":\s*(\d+),.*?"type":\s*"message".*?"text":\s*(\[.*?\]|"[^"]*").*?\}'
            messages = re.finditer(message_pattern, content, re.DOTALL)

            count = 0
            for match in messages:
                msg_id = int(match.group(1))
                text_raw = match.group(2)

                # Обрабатываем текст
                text = self._extract_text_from_raw(text_raw)

                if text and len(text.strip()) > 10:
                    self.messages.append({
                        'id': msg_id,
                        'text': text,
                        'type': 'message'
                    })
                    count += 1

            print(f"✓ Извлечено {count} сообщений частичным методом")
            return count > 0

        except Exception as e:
            print(f"Ошибка при частичном извлечении: {e}")
            return False

    def _extract_text_from_raw(self, text_raw: str) -> str:
        """Извлекает чистый текст из сырых данных"""
        if text_raw.startswith('"') and text_raw.endswith('"'):
            # Простая строка
            return text_raw[1:-1]
        elif text_raw.startswith('['):
            # Массив объектов
            try:
                text_array = json.loads(text_raw)
                result = ""
                for item in text_array:
                    if isinstance(item, str):
                        result += item
                    elif isinstance(item, dict) and 'text' in item:
                        result += item['text']
                return result
            except:
                # Извлекаем текст регулярными выражениями
                text_parts = re.findall(r'"text":\s*"([^"]*)"', text_raw)
                return ''.join(text_parts)

        return ""

    def _extract_data(self, data: Dict[str, Any]):
        """Извлекает данные из корректно загруженного JSON"""
        self.channel_info = {
            'name': data.get('name', ''),
            'type': data.get('type', ''),
            'id': data.get('id', 0)
        }

        messages = data.get('messages', [])
        for msg in messages:
            if msg.get('type') == 'message' and msg.get('text'):
                text = self._extract_text_from_telegram_format(msg['text'])
                if text and len(text.strip()) > 10:
                    self.messages.append({
                        'id': msg.get('id'),
                        'text': text,
                        'type': 'message',
                        'date': msg.get('date', ''),
                        'from': msg.get('from', '')
                    })

    def _extract_text_from_telegram_format(self, text_data) -> str:
        """Извлекает текст из формата Telegram"""
        if isinstance(text_data, str):
            return text_data
        elif isinstance(text_data, list):
            result = ""
            for item in text_data:
                if isinstance(item, str):
                    result += item
                elif isinstance(item, dict) and 'text' in item:
                    result += item['text']
            return result
        return str(text_data)

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику загруженных данных"""
        if not self.messages:
            return {"error": "Нет загруженных сообщений"}

        total_messages = len(self.messages)
        total_chars = sum(len(msg['text']) for msg in self.messages)
        avg_length = total_chars / total_messages if total_messages > 0 else 0

        # Анализ слов
        all_words = []
        for msg in self.messages:
            words = re.findall(r'\b\w+\b', msg['text'].lower())
            all_words.extend(words)

        unique_words = len(set(all_words))

        return {
            'channel_name': self.channel_info.get('name', 'Unknown'),
            'channel_type': self.channel_info.get('type', 'Unknown'),
            'channel_id': self.channel_info.get('id', 0),
            'total_messages': total_messages,
            'total_characters': total_chars,
            'average_message_length': round(avg_length, 1),
            'total_words': len(all_words),
            'unique_words': unique_words
        }

    def generate_simple_report(self) -> str:
        """Генерирует простой отчет"""
        stats = self.get_statistics()

        if "error" in stats:
            return f"Ошибка: {stats['error']}"

        report = f"""
# Анализ Telegram канала: {stats['channel_name']}

## Основная информация
- **Название канала:** {stats['channel_name']}
- **Тип:** {stats['channel_type']}
- **ID:** {stats['channel_id']}

## Статистика сообщений
- **Всего сообщений:** {stats['total_messages']}
- **Общее количество символов:** {stats['total_characters']:,}
- **Средняя длина сообщения:** {stats['average_message_length']} символов
- **Всего слов:** {stats['total_words']:,}
- **Уникальных слов:** {stats['unique_words']:,}

## Примеры сообщений
"""

        # Добавляем примеры сообщений
        for i, msg in enumerate(self.messages[:5], 1):
            text_preview = msg['text'][:200] + "..." if len(msg['text']) > 200 else msg['text']
            report += f"\n### Сообщение {i}\n{text_preview}\n"

        return report

def main():
    print("=== Устойчивый анализатор Telegram экспорта ===")

    analyzer = RobustTelegramAnalyzer("result.json")

    if analyzer.try_load_json():
        print("\n=== Статистика ===")
        stats = analyzer.get_statistics()

        for key, value in stats.items():
            print(f"{key}: {value}")

        # Генерируем отчет
        report = analyzer.generate_simple_report()

        # Сохраняем отчет
        with open("telegram_analysis_robust.md", "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n✓ Отчет сохранен в файл: telegram_analysis_robust.md")

        # Сохраняем извлеченные данные в формате, совместимом со старым анализатором
        compatible_data = []
        for msg in analyzer.messages:
            compatible_data.append({
                'channel_id': analyzer.channel_info.get('id', 0),
                'message_id': msg['id'],
                'media_url': [],
                'data_text': msg['text']
            })

        with open("extracted_messages.json", "w", encoding="utf-8") as f:
            json.dump(compatible_data, f, ensure_ascii=False, indent=2)

        print(f"✓ Данные сохранены в совместимом формате: extracted_messages.json")

    else:
        print("✗ Не удалось загрузить данные из файла")

if __name__ == "__main__":
    main()
