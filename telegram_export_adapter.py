"""
Адаптер для работы с новым форматом экспорта Telegram Desktop
Обрабатывает сложную структуру данных и устраняет дублирование текста
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any, Set
import hashlib

class TelegramExportAdapter:
    def __init__(self, export_file_path: str):
        self.export_file_path = export_file_path
        self.raw_data = None
        self.processed_messages = []
        self.seen_texts = set()  # Для дедупликации

    def load_data(self) -> Dict[str, Any]:
        """Загрузка данных из файла экспорта"""
        with open(self.export_file_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)

        print(f"Загружен канал: {self.raw_data.get('name', 'Unknown')}")
        print(f"Тип: {self.raw_data.get('type', 'Unknown')}")
        print(f"ID: {self.raw_data.get('id', 'Unknown')}")
        print(f"Всего записей: {len(self.raw_data.get('messages', []))}")

        return self.raw_data

    def extract_text_from_complex_structure(self, text_data: Any) -> str:
        """
        Извлекает чистый текст из сложной структуры Telegram
        Обрабатывает как простые строки, так и массивы объектов
        """
        if isinstance(text_data, str):
            return text_data

        if isinstance(text_data, list):
            result_parts = []
            for item in text_data:
                if isinstance(item, str):
                    result_parts.append(item)
                elif isinstance(item, dict):
                    # Обрабатываем различные типы объектов
                    if 'text' in item:
                        result_parts.append(item['text'])
                    elif 'type' in item and item['type'] == 'plain' and 'text' in item:
                        result_parts.append(item['text'])

            return ''.join(result_parts)

        return str(text_data) if text_data else ""

    def create_text_hash(self, text: str) -> str:
        """Создает хеш для дедупликации текста"""
        # Нормализуем текст для сравнения
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def is_duplicate_text(self, text: str, min_length: int = 50) -> bool:
        """
        Проверяет, является ли текст дубликатом
        Игнорирует очень короткие сообщения
        """
        if len(text) < min_length:
            return False

        text_hash = self.create_text_hash(text)

        if text_hash in self.seen_texts:
            return True

        self.seen_texts.add(text_hash)
        return False

    def extract_media_info(self, message: Dict[str, Any]) -> List[str]:
        """Извлекает информацию о медиафайлах"""
        media_urls = []

        # Проверяем различные поля с медиа
        media_fields = ['photo', 'video', 'file', 'sticker', 'voice_message', 'video_message']

        for field in media_fields:
            if field in message and message[field]:
                if isinstance(message[field], str):
                    media_urls.append(message[field])
                elif isinstance(message[field], dict) and 'file' in message[field]:
                    media_urls.append(message[field]['file'])

        return media_urls

    def process_messages(self) -> List[Dict[str, Any]]:
        """
        Обрабатывает сообщения и конвертирует в унифицированный формат
        Устраняет дублирование и нормализует структуру
        """
        if not self.raw_data:
            self.load_data()

        messages = self.raw_data.get('messages', [])
        processed_count = 0
        duplicate_count = 0
        service_count = 0

        for message in messages:
            # Пропускаем служебные сообщения
            if message.get('type') == 'service':
                service_count += 1
                continue

            # Извлекаем текст
            raw_text = message.get('text', '')
            clean_text = self.extract_text_from_complex_structure(raw_text)

            # Пропускаем пустые сообщения
            if not clean_text or len(clean_text.strip()) < 10:
                continue

            # Проверяем на дублирование
            if self.is_duplicate_text(clean_text):
                duplicate_count += 1
                continue

            # Извлекаем медиа
            media_urls = self.extract_media_info(message)

            # Создаем унифицированную структуру
            processed_message = {
                'channel_id': self.raw_data.get('id'),
                'message_id': message.get('id'),
                'date': message.get('date'),
                'date_unixtime': message.get('date_unixtime'),
                'from': message.get('from', ''),
                'from_id': message.get('from_id', ''),
                'data_text': clean_text,
                'media_url': media_urls,
                'type': message.get('type', 'message'),
                'edited': message.get('edited'),
                'reactions_count': self.count_reactions(message.get('reactions', []))
            }

            self.processed_messages.append(processed_message)
            processed_count += 1

        print(f"\nОбработка завершена:")
        print(f"- Обработано сообщений: {processed_count}")
        print(f"- Пропущено дубликатов: {duplicate_count}")
        print(f"- Пропущено служебных: {service_count}")
        print(f"- Всего уникальных текстов: {len(self.seen_texts)}")

        return self.processed_messages

    def count_reactions(self, reactions: List[Dict[str, Any]]) -> int:
        """Подсчитывает общее количество реакций"""
        total = 0
        for reaction in reactions:
            total += reaction.get('count', 0)
        return total

    def get_channel_info(self) -> Dict[str, Any]:
        """Возвращает информацию о канале"""
        if not self.raw_data:
            return {}

        return {
            'name': self.raw_data.get('name'),
            'type': self.raw_data.get('type'),
            'id': self.raw_data.get('id'),
            'total_messages': len(self.raw_data.get('messages', [])),
            'processed_messages': len(self.processed_messages)
        }

    def save_processed_data(self, output_path: str = None) -> str:
        """Сохраняет обработанные данные в формате, совместимом со старым анализатором"""
        if not self.processed_messages:
            self.process_messages()

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"processed_export_{timestamp}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.processed_messages, f, ensure_ascii=False, indent=2)

        print(f"Обработанные данные сохранены в: {output_path}")
        return output_path

    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику обработки"""
        if not self.processed_messages:
            return {}

        # Анализ по годам
        years = {}
        for msg in self.processed_messages:
            if msg.get('date'):
                try:
                    year = datetime.fromisoformat(msg['date'].replace('T', ' ').replace('Z', '')).year
                    years[year] = years.get(year, 0) + 1
                except:
                    pass

        # Анализ длины сообщений
        text_lengths = [len(msg['data_text']) for msg in self.processed_messages]

        return {
            'total_processed': len(self.processed_messages),
            'unique_texts': len(self.seen_texts),
            'years_distribution': years,
            'avg_text_length': sum(text_lengths) / len(text_lengths) if text_lengths else 0,
            'max_text_length': max(text_lengths) if text_lengths else 0,
            'min_text_length': min(text_lengths) if text_lengths else 0
        }

# Пример использования
if __name__ == "__main__":
    adapter = TelegramExportAdapter("result.json")
    adapter.load_data()
    processed_data = adapter.process_messages()

    # Сохраняем обработанные данные
    output_file = adapter.save_processed_data()

    # Выводим статистику
    stats = adapter.get_statistics()
    print("\nСтатистика обработки:")
    for key, value in stats.items():
        print(f"{key}: {value}")
