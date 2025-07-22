"""
Основной скрипт для полного анализа Telegram канала
Запускает весь пайплайн: предобработку -> анализ -> генерацию отчета
"""

import os
import sys
from telegram_analyzer import TelegramAnalyzer
from report_generator import ReportGenerator

def install_requirements():
    """Установка необходимых библиотек"""
    print("Проверяем и устанавливаем необходимые библиотеки...")

    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        print("✓ NLTK данные загружены")
    except ImportError:
        print("Установите nltk: pip install nltk")
        return False

    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'seaborn', 'scikit-learn',
        'pymorphy2', 'wordcloud', 'textblob', 'dostoevsky'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} - не установлен")

    if missing_packages:
        print(f"\nУстановите недостающие пакеты:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True

def main():
    print("="*60)
    print("КОМПЛЕКСНЫЙ АНАЛИЗ TELEGRAM КАНАЛА")
    print("="*60)

    # Проверка зависимостей
    if not install_requirements():
        print("\nОшибка: не все зависимости установлены")
        return

    # Проверка наличия файла данных
    data_file = 'parsed_data_20250722_114557.json'
    if not os.path.exists(data_file):
        print(f"\nОшибка: файл {data_file} не найден!")
        return

    print(f"\n📁 Найден файл данных: {data_file}")

    try:
        # Этап 1: Анализ данных
        print("\n" + "="*60)
        print("ЭТАП 1: АНАЛИЗ ДАННЫХ")
        print("="*60)

        analyzer = TelegramAnalyzer(data_file)
        analyzer.load_data()
        analyzer.preprocess_texts()
        report_data = analyzer.generate_report_data()

        print("\n✓ Анализ данных завершен успешно!")
        print("Созданы файлы:")
        print("  - frequency_analysis.png")
        print("  - topic_modeling.png")
        print("  - sentiment_analysis.png")
        print("  - analysis_report_data.json")

        # Этап 2: Генерация отчета
        print("\n" + "="*60)
        print("ЭТАП 2: ГЕНЕРАЦИЯ ОТЧЕТА")
        print("="*60)

        generator = ReportGenerator()

        # Спрашиваем пользователя о использовании LLM
        use_llm = input("\nИспользовать LLM для генерации отчета? (y/n): ").lower() == 'y'

        if use_llm:
            api_key = input("Введите OpenAI API ключ (или Enter для использования переменной окружения): ").strip()
            if api_key:
                import openai
                openai.api_key = api_key

        report, filename = generator.generate_full_report(use_llm=use_llm)

        print(f"\n✓ Отчет создан: {filename}")

        # Краткая сводка результатов
        print("\n" + "="*60)
        print("СВОДКА РЕЗУЛЬТАТОВ")
        print("="*60)

        print(f"📊 Проанализировано сообщений: {report_data['general_stats']['total_messages']}")
        print(f"📝 Средняя длина сообщения: {report_data['general_stats']['average_message_length']:.1f} символов")
        print(f"🔤 Обработано слов: {report_data['general_stats']['total_words_processed']}")

        print(f"\n📈 Тональность:")
        for sentiment, percentage in report_data['sentiment_percentage'].items():
            print(f"  - {sentiment}: {percentage:.1f}%")

        print(f"\n🏷️ Основные темы:")
        for i, topic in enumerate(report_data['topics'][:3], 1):
            words = ', '.join(topic['words'][:5])
            print(f"  {i}. {words}")

        print(f"\n📄 Все результаты сохранены в текущей директории")
        print(f"📋 Итоговый отчет: {filename}")

    except Exception as e:
        print(f"\nОшибка при выполнении анализа: {e}")
        print("Проверьте:")
        print("1. Корректность формата JSON файла")
        print("2. Установку всех зависимостей")
        print("3. Наличие прав на запись в текущую директорию")

        import traceback
        print(f"\nПолная информация об ошибке:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
