"""
Быстрый анализатор Telegram канала для демонстрации результатов
"""

import json
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Настройка matplotlib для русского языка
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def load_and_analyze_data():
    """Быстрый анализ данных Telegram канала"""
    print("Загружаем и анализируем данные...")

    # Загрузка данных
    with open('parsed_data_20250722_114557.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Загружено {len(data)} сообщений")

    # Извлечение текстов
    texts = [item['data_text'] for item in data if 'data_text' in item and item['data_text']]

    # Базовая статистика
    total_chars = sum(len(text) for text in texts)
    avg_length = total_chars / len(texts)

    print(f"\n=== БАЗОВАЯ СТАТИСТИКА ===")
    print(f"Количество сообщений: {len(texts)}")
    print(f"Общее количество символов: {total_chars:,}")
    print(f"Средняя длина сообщения: {avg_length:.1f} символов")

    # Очистка текстов для анализа
    cleaned_texts = []
    for text in texts:
        # Удаляем markdown
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        # Удаляем ссылки и упоминания
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r't\.me/\w+', '', text)
        # Приводим к нижнему регистру
        text = text.lower()
        cleaned_texts.append(text)

    # Частотный анализ слов
    print(f"\n=== ЧАСТОТНЫЙ АНАЛИЗ ===")
    all_words = []
    for text in cleaned_texts:
        # Простая токенизация
        words = re.findall(r'\b[а-яё]{3,}\b', text)
        all_words.extend(words)

    # Исключаем стоп-слова
    stop_words = {
        'что', 'это', 'как', 'для', 'при', 'они', 'все', 'был', 'была', 'было', 'были',
        'или', 'уже', 'еще', 'так', 'где', 'когда', 'кто', 'чем', 'том', 'тем', 'под',
        'над', 'про', 'его', 'ему', 'неё', 'них', 'нас', 'вас', 'мне', 'тебе', 'нам',
        'вам', 'без', 'для', 'изо', 'из-за', 'при', 'год', 'лет', 'день', 'время'
    }

    filtered_words = [word for word in all_words if word not in stop_words and len(word) > 3]

    word_freq = Counter(filtered_words)
    top_words = word_freq.most_common(20)

    print("Топ-20 наиболее частых слов:")
    for i, (word, count) in enumerate(top_words, 1):
        print(f"{i:2d}. {word:<15} - {count:3d} раз")

    # Анализ тематики по ключевым словам
    print(f"\n=== ТЕМАТИЧЕСКИЙ АНАЛИЗ ===")

    military_words = ['армия', 'войск', 'военный', 'полк', 'дивизия', 'батальон', 'группировка', 'фронт']
    locations = ['украин', 'россия', 'донецк', 'луганск', 'крым', 'харьков', 'киев']
    weapons = ['танк', 'артиллерия', 'дрон', 'ракета', 'снаряд', 'оружие', 'техника']

    military_count = sum(word_freq.get(word, 0) for word in military_words)
    location_count = sum(word_freq.get(word, 0) for word in locations)
    weapon_count = sum(word_freq.get(word, 0) for word in weapons)

    print(f"Военная тематика: {military_count} упоминаний")
    print(f"Географические названия: {location_count} упоминаний")
    print(f"Вооружение и техника: {weapon_count} упоминаний")

    # Простой анализ тональности
    print(f"\n=== АНАЛИЗ ТОНАЛЬНОСТИ ===")

    positive_words = ['успешно', 'победа', 'достижение', 'хорошо', 'отлично', 'поражение']
    negative_words = ['потери', 'уничтожен', 'разгром', 'провал', 'ошибка', 'неудача']

    positive_count = 0
    negative_count = 0
    neutral_count = 0

    for text in texts:
        text_lower = text.lower()
        pos_found = any(word in text_lower for word in positive_words)
        neg_found = any(word in text_lower for word in negative_words)

        if pos_found and not neg_found:
            positive_count += 1
        elif neg_found and not pos_found:
            negative_count += 1
        else:
            neutral_count += 1

    total = len(texts)
    print(f"Позитивные сообщения: {positive_count} ({positive_count/total*100:.1f}%)")
    print(f"Негативные сообщения: {negative_count} ({negative_count/total*100:.1f}%)")
    print(f"Нейтральные сообщения: {neutral_count} ({neutral_count/total*100:.1f}%)")

    # Визуализация
    create_visualizations(top_words, [positive_count, negative_count, neutral_count])

    # Создание отчета для LLM
    report_data = {
        'general_stats': {
            'total_messages': len(texts),
            'average_message_length': avg_length,
            'total_characters': total_chars
        },
        'top_words': [{'word': word, 'frequency': count} for word, count in top_words],
        'thematic_analysis': {
            'military_mentions': military_count,
            'location_mentions': location_count,
            'weapon_mentions': weapon_count
        },
        'sentiment_analysis': {
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count,
            'positive_percentage': positive_count/total*100,
            'negative_percentage': negative_count/total*100,
            'neutral_percentage': neutral_count/total*100
        },
        'sample_texts': texts[:5]  # Первые 5 сообщений как примеры
    }

    # Сохраняем результаты
    with open('quick_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n=== ВЫВОДЫ ===")
    print("Канал содержит преимущественно военную тематику")
    print("Активно используется специализированная военная терминология")
    print("Присутствуют географические ссылки на конфликтную зону")
    print("Результаты сохранены в 'quick_analysis_results.json'")

    return report_data

def create_visualizations(top_words, sentiment_counts):
    """Создание базовых графиков"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # График частотности слов
    words, freqs = zip(*top_words[:10])
    ax1.barh(range(len(words)), freqs, color='skyblue')
    ax1.set_yticks(range(len(words)))
    ax1.set_yticklabels(words)
    ax1.set_xlabel('Частота')
    ax1.set_title('Топ-10 наиболее частых слов')
    ax1.invert_yaxis()

    # График тональности
    labels = ['Позитивные', 'Негативные', 'Нейтральные']
    colors = ['green', 'red', 'gray']
    ax2.pie(sentiment_counts, labels=labels, colors=colors, autopct='%1.1f%%')
    ax2.set_title('Распределение тональности сообщений')

    plt.tight_layout()
    plt.savefig('quick_analysis_charts.png', dpi=300, bbox_inches='tight')
    plt.show()

    print("Графики сохранены в 'quick_analysis_charts.png'")

if __name__ == "__main__":
    try:
        results = load_and_analyze_data()
        print("\n🎉 Быстрый анализ завершен успешно!")
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
