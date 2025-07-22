"""
Генератор отчетов для анализа Telegram канала с использованием LLM
"""

import json
import openai
from datetime import datetime
import os

class ReportGenerator:
    def __init__(self, api_key=None):
        """
        Инициализация генератора отчетов
        api_key: API ключ для OpenAI (или другой LLM сервис)
        """
        if api_key:
            openai.api_key = api_key
        else:
            # Попытка получить ключ из переменных окружения
            openai.api_key = os.getenv('OPENAI_API_KEY')

    def load_analysis_data(self, json_file='analysis_report_data.json'):
        """Загрузка данных анализа"""
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_prompt(self, analysis_data):
        """Создание промпта для LLM на основе данных анализа"""

        prompt = f"""
Проанализируй данные Telegram канала и составь подробный отчет о контенте, тематике и позиции автора.

СТАТИСТИЧЕСКИЕ ДАННЫЕ:
- Общее количество сообщений: {analysis_data['general_stats']['total_messages']}
- Средняя длина сообщения: {analysis_data['general_stats']['average_message_length']:.1f} символов
- Общее количество обработанных слов: {analysis_data['general_stats']['total_words_processed']}

ЧАСТОТНЫЙ АНАЛИЗ - ТОП СЛОВ:
{self._format_top_words(analysis_data['top_words'])}

ТЕМАТИЧЕСКОЕ МОДЕЛИРОВАНИЕ:
{self._format_topics(analysis_data['topics'])}

АНАЛИЗ ТОНАЛЬНОСТИ:
- Распределение по тональности:
  * Позитивные: {analysis_data['sentiment_percentage'].get('positive', 0):.1f}%
  * Негативные: {analysis_data['sentiment_percentage'].get('negative', 0):.1f}%
  * Нейтральные: {analysis_data['sentiment_percentage'].get('neutral', 0):.1f}%

ПРИМЕРЫ СООБЩЕНИЙ:

Позитивные сообщения:
{self._format_sample_messages(analysis_data['sample_messages']['positive'])}

Негативные сообщения:
{self._format_sample_messages(analysis_data['sample_messages']['negative'])}

Нейтральные сообщения:
{self._format_sample_messages(analysis_data['sample_messages']['neutral'])}

ЗАДАЧА:
На основе этих данных составь развернутый аналитический отчет, который должен включать:

1. ОБЩАЯ ХАРАКТЕРИСТИКА КАНАЛА
   - Тип контента и его специфика
   - Целевая аудитория
   - Стиль подачи материала

2. ОСНОВНЫЕ ТЕМЫ И НАПРАВЛЕНИЯ
   - Детальный анализ выявленных тематических кластеров
   - Приоритетные направления контента
   - Связь между темами

3. ПОЗИЦИЯ И НАСТРОЕНИЯ АВТОРА
   - Политические и идеологические взгляды
   - Отношение к различным событиям и явлениям
   - Эмоциональная окраска контента

4. ЯЗЫКОВЫЕ ОСОБЕННОСТИ
   - Характерная лексика и терминология
   - Стилистические приемы
   - Способы воздействия на аудиторию

5. ВЫВОДЫ И РЕКОМЕНДАЦИИ
   - Общая характеристика канала
   - Потенциальные риски или особенности
   - Рекомендации по мониторингу

Отчет должен быть объективным, основанным на данных, и содержать конкретные примеры.
"""
        return prompt

    def _format_top_words(self, top_words):
        """Форматирование топ слов для промпта"""
        formatted = []
        for i, word_data in enumerate(top_words[:10], 1):
            formatted.append(f"{i}. {word_data['word']} ({word_data['frequency']} раз)")
        return '\n'.join(formatted)

    def _format_topics(self, topics):
        """Форматирование тем для промпта"""
        formatted = []
        for i, topic in enumerate(topics, 1):
            words = ', '.join(topic['words'][:8])
            formatted.append(f"Тема {i}: {words}")
        return '\n'.join(formatted)

    def _format_sample_messages(self, messages):
        """Форматирование примеров сообщений"""
        if not messages:
            return "Примеры отсутствуют"

        formatted = []
        for i, msg in enumerate(messages[:2], 1):
            formatted.append(f"{i}. {msg}")
        return '\n'.join(formatted)

    def generate_report_with_openai(self, analysis_data, model="gpt-4"):
        """Генерация отчета с помощью OpenAI API"""
        try:
            prompt = self.create_prompt(analysis_data)

            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Ты опытный аналитик контента и социальных медиа. Твоя задача - провести глубокий анализ Telegram канала на основе предоставленных данных."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Ошибка при генерации отчета через OpenAI: {e}")
            return self.generate_basic_report(analysis_data)

    def generate_basic_report(self, analysis_data):
        """Базовый отчет без использования LLM"""
        report = f"""
# АНАЛИТИЧЕСКИЙ ОТЧЕТ ПО TELEGRAM КАНАЛУ
Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}

## 1. ОБЩАЯ СТАТИСТИКА
- Проанализировано сообщений: {analysis_data['general_stats']['total_messages']}
- Средняя длина сообщения: {analysis_data['general_stats']['average_message_length']:.1f} символов
- Обработано уникальных слов: {analysis_data['general_stats']['total_words_processed']}

## 2. ЧАСТОТНЫЙ АНАЛИЗ
### Наиболее употребляемые слова:
"""
        for i, word_data in enumerate(analysis_data['top_words'][:10], 1):
            report += f"{i}. **{word_data['word']}** - {word_data['frequency']} упоминаний\n"

        report += "\n## 3. ТЕМАТИЧЕСКОЕ МОДЕЛИРОВАНИЕ\n"
        for i, topic in enumerate(analysis_data['topics'], 1):
            words = ', '.join(topic['words'][:8])
            report += f"**Тема {i}:** {words}\n"

        report += f"""
## 4. АНАЛИЗ ТОНАЛЬНОСТИ
- Позитивные сообщения: {analysis_data['sentiment_percentage'].get('positive', 0):.1f}%
- Негативные сообщения: {analysis_data['sentiment_percentage'].get('negative', 0):.1f}%
- Нейтральные сообщения: {analysis_data['sentiment_percentage'].get('neutral', 0):.1f}%

## 5. ПРЕДВАРИТЕЛЬНЫЕ ВЫВОДЫ
На основе анализа данных можно сделать следующие выводы:
- Канал характеризуется определенной тематической направленностью
- Присутствует выраженная эмоциональная окраска контента
- Используется специфическая терминология и лексика

*Для более детального анализа рекомендуется использование LLM модели*
"""
        return report

    def save_report(self, report_text, filename='telegram_channel_report.md'):
        """Сохранение отчета в файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"Отчет сохранен в файл: {filename}")

    def generate_full_report(self, use_llm=True, api_key=None):
        """Генерация полного отчета"""
        if api_key:
            self.api_key = api_key

        # Загружаем данные анализа
        analysis_data = self.load_analysis_data()

        # Генерируем отчет
        if use_llm and openai.api_key:
            print("Генерируем отчет с помощью LLM...")
            report = self.generate_report_with_openai(analysis_data)
        else:
            print("Генерируем базовый отчет...")
            report = self.generate_basic_report(analysis_data)

        # Сохраняем отчет
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'telegram_report_{timestamp}.md'
        self.save_report(report, filename)

        return report, filename

def main():
    """Основная функция для запуска генератора отчетов"""
    generator = ReportGenerator()

    # Проверяем наличие файла с данными анализа
    if not os.path.exists('analysis_report_data.json'):
        print("Файл analysis_report_data.json не найден!")
        print("Сначала запустите telegram_analyzer.py для проведения анализа")
        return

    # Генерируем отчет
    try:
        report, filename = generator.generate_full_report(use_llm=True)
        print(f"\nОтчет успешно создан: {filename}")
        print("\nПревью отчета:")
        print("="*50)
        print(report[:500] + "..." if len(report) > 500 else report)
        print("="*50)

    except Exception as e:
        print(f"Ошибка при генерации отчета: {e}")
        print("Создаем базовый отчет...")
        report, filename = generator.generate_full_report(use_llm=False)

if __name__ == "__main__":
    main()
