"""
Система обработки Telegram экспортов с удобным интерфейсом
Поддерживает различные форматы и автоматически генерирует отчеты
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import hashlib

# Импортируем наши анализаторы
from robust_analyzer import RobustTelegramAnalyzer
from improved_analyzer import analyze_extracted_data

class TelegramProcessingSystem:
    def __init__(self, base_dir="M:/Projects/Pycharm_projects/GPT_API_test"):
        self.base_dir = Path(base_dir)
        self.uploads_dir = self.base_dir / "uploads"
        self.reports_dir = self.base_dir / "reports"
        self.temp_dir = self.base_dir / "temp"

        # Создаем необходимые папки
        self.uploads_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

        print("🚀 Система обработки Telegram экспортов готова к работе!")
        print(f"📁 Базовая директория: {self.base_dir}")

    def process_file(self, file_path, custom_name=None):
        """
        Универсальная обработка файла Telegram экспорта
        Автоматически определяет формат и генерирует отчет
        """
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"❌ Файл не найден: {file_path}")
            return None

        print(f"📄 Обрабатываем файл: {file_path.name}")

        # Создаем уникальный ID для обработки
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = self._get_file_hash(file_path)[:8]
        process_id = f"{timestamp}_{file_hash}"

        if custom_name:
            process_id = f"{timestamp}_{custom_name}"

        try:
            # Копируем файл в uploads
            uploaded_file = self.uploads_dir / f"{process_id}_{file_path.name}"
            shutil.copy2(file_path, uploaded_file)
            print(f"✅ Файл загружен: {uploaded_file.name}")

            # Обрабатываем файл
            return self._analyze_file(uploaded_file, process_id)

        except Exception as e:
            print(f"❌ Ошибка при обработке файла: {e}")
            return None

    def _get_file_hash(self, file_path):
        """Создает хеш файла для уникального ID"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _analyze_file(self, file_path, process_id):
        """Анализирует файл и генерирует отчеты"""
        print(f"🔍 Начинаем анализ файла...")

        # Определяем тип файла и обрабатываем
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Проверяем формат
            if isinstance(data, dict) and 'messages' in data:
                print("📱 Обнаружен экспорт Telegram Desktop")
                return self._process_telegram_export(file_path, process_id, data)
            elif isinstance(data, list) and len(data) > 0 and 'channel_id' in data[0]:
                print("📊 Обнаружен старый формат данных")
                return self._process_old_format(file_path, process_id, data)
            else:
                print("❓ Неизвестный формат файла, попробуем универсальную обработку")
                return self._process_unknown_format(file_path, process_id)

        except json.JSONDecodeError:
            print("⚠️ Файл содержит ошибки JSON, используем устойчивый парсер")
            return self._process_damaged_json(file_path, process_id)

    def _process_telegram_export(self, file_path, process_id, data):
        """Обрабатываем экспорт Telegram Desktop"""
        # Используем устойчивый анализатор
        analyzer = RobustTelegramAnalyzer(str(file_path))

        if analyzer.try_load_json():
            # Сохраняем извлеченные данные
            extracted_file = self.temp_dir / f"{process_id}_extracted.json"
            compatible_data = []

            for msg in analyzer.messages:
                compatible_data.append({
                    'channel_id': analyzer.channel_info.get('id', 0),
                    'message_id': msg['id'],
                    'media_url': [],
                    'data_text': msg['text']
                })

            with open(extracted_file, 'w', encoding='utf-8') as f:
                json.dump(compatible_data, f, ensure_ascii=False, indent=2)

            # Генерируем отчет
            return self._generate_report(extracted_file, process_id, analyzer.channel_info)

        return None

    def _process_old_format(self, file_path, process_id, data):
        """Обрабатываем старый формат данных"""
        # Копируем во временную папку для анализа
        temp_file = self.temp_dir / f"{process_id}_extracted.json"
        shutil.copy2(file_path, temp_file)

        # Определяем информацию о канале
        channel_info = {
            'id': data[0].get('channel_id', 0) if data else 0,
            'name': 'Unknown Channel',
            'type': 'unknown'
        }

        return self._generate_report(temp_file, process_id, channel_info)

    def _process_damaged_json(self, file_path, process_id):
        """Обрабатываем поврежденный JSON"""
        analyzer = RobustTelegramAnalyzer(str(file_path))

        if analyzer.try_load_json():
            # Сохраняем извлеченные данные
            extracted_file = self.temp_dir / f"{process_id}_extracted.json"
            compatible_data = []

            for msg in analyzer.messages:
                compatible_data.append({
                    'channel_id': analyzer.channel_info.get('id', 0),
                    'message_id': msg['id'],
                    'media_url': [],
                    'data_text': msg['text']
                })

            with open(extracted_file, 'w', encoding='utf-8') as f:
                json.dump(compatible_data, f, ensure_ascii=False, indent=2)

            return self._generate_report(extracted_file, process_id, analyzer.channel_info)

        return None

    def _process_unknown_format(self, file_path, process_id):
        """Пытаемся обработать неизвестный формат"""
        print("🔧 Попытка обработки неизвестного формата...")
        return self._process_damaged_json(file_path, process_id)

    def _generate_report(self, data_file, process_id, channel_info):
        """Генерирует финальный отчет"""
        print("📊 Генерируем отчет...")

        # Копируем файл данных как extracted_messages.json для анализатора
        current_extracted = self.base_dir / "extracted_messages.json"
        shutil.copy2(data_file, current_extracted)

        # Запускаем анализ
        success = analyze_extracted_data()

        if success:
            # Перемещаем отчет в папку отчетов
            current_report = self.base_dir / "final_analysis_report.md"
            final_report = self.reports_dir / f"report_{process_id}.md"

            if current_report.exists():
                shutil.move(current_report, final_report)

                # Создаем сводку
                summary = self._create_summary(final_report, process_id, channel_info)

                print(f"✅ Отчет готов: {final_report.name}")
                print(f"📋 Сводка: {summary}")

                return {
                    'process_id': process_id,
                    'report_file': str(final_report),
                    'data_file': str(data_file),
                    'channel_info': channel_info,
                    'summary': summary
                }

        print("❌ Не удалось сгенерировать отчет")
        return None

    def _create_summary(self, report_file, process_id, channel_info):
        """Создает краткую сводку анализа"""
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Извлекаем ключевые метрики
            stats = {}

            # Ищем статистики в отчете
            import re

            total_match = re.search(r'\*\*Всего сообщений:\*\* (\d+)', content)
            if total_match:
                stats['total_messages'] = int(total_match.group(1))

            chars_match = re.search(r'\*\*Общее количество символов:\*\* ([\d,]+)', content)
            if chars_match:
                stats['total_chars'] = chars_match.group(1)

            words_match = re.search(r'\*\*Всего слов:\*\* ([\d,]+)', content)
            if words_match:
                stats['total_words'] = words_match.group(1)

            unique_match = re.search(r'\*\*Уникальных слов:\*\* ([\d,]+)', content)
            if unique_match:
                stats['unique_words'] = unique_match.group(1)

            # Топ слово
            top_word_match = re.search(r'1\. \*\*([^*]+)\*\* — (\d+) раз', content)
            if top_word_match:
                stats['top_word'] = f"{top_word_match.group(1)} ({top_word_match.group(2)})"

            summary = f"""
🎯 СВОДКА АНАЛИЗА
Canal: {channel_info.get('name', 'Unknown')}
📊 Сообщений: {stats.get('total_messages', 'N/A')}
📝 Слов: {stats.get('total_words', 'N/A')} (уникальных: {stats.get('unique_words', 'N/A')})
🔥 Топ слово: {stats.get('top_word', 'N/A')}
📄 Символов: {stats.get('total_chars', 'N/A')}
"""

            return summary

        except Exception as e:
            return f"Ошибка создания сводки: {e}"

    def list_reports(self):
        """Показывает список всех отчетов"""
        reports = list(self.reports_dir.glob("report_*.md"))

        if not reports:
            print("📁 Отчетов пока нет")
            return

        print(f"📋 Найдено отчетов: {len(reports)}")
        for report in sorted(reports, reverse=True):
            size = report.stat().st_size / 1024  # KB
            modified = datetime.fromtimestamp(report.stat().st_mtime)
            print(f"  📄 {report.name} ({size:.1f} KB, {modified.strftime('%d.%m.%Y %H:%M')})")

    def get_report(self, process_id):
        """Возвращает путь к отчету по ID"""
        report_file = self.reports_dir / f"report_{process_id}.md"
        if report_file.exists():
            return str(report_file)
        return None

def main():
    """Главная функция для демонстрации использования"""
    processor = TelegramProcessingSystem()

    print("\n" + "="*50)
    print("🎯 СИСТЕМА АНАЛИЗА TELEGRAM КАНАЛОВ")
    print("="*50)

    # Пример обработки файла result.json
    result = processor.process_file("result.json", "denis_sexy_it")

    if result:
        print(f"\n🎉 Обработка завершена!")
        print(f"📊 ID процесса: {result['process_id']}")
        print(f"📄 Отчет: {result['report_file']}")
        print(result['summary'])

    print("\n📋 Список всех отчетов:")
    processor.list_reports()

if __name__ == "__main__":
    main()
