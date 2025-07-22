"""
Финальный анализатор для извлеченных данных Telegram канала
"""

import json
import re
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

def analyze_extracted_data():
    """Анализирует извлеченные данные из extracted_messages.json"""
    try:
        # Загружаем извлеченные данные
        with open('extracted_messages.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"=== Анализ канала Denis Sexy IT 🤖 ===")
        print(f"Загружено сообщений: {len(data)}")

        # Извлекаем тексты
        texts = [item['data_text'] for item in data if item['data_text'] and len(item['data_text']) > 10]
        print(f"Сообщений для анализа: {len(texts)}")

        # Базовая статистика
        total_chars = sum(len(text) for text in texts)
        avg_length = total_chars / len(texts) if texts else 0

        print(f"\n=== Статистика текста ===")
        print(f"Общее количество символов: {total_chars:,}")
        print(f"Средняя длина сообщения: {avg_length:.1f} символов")
        print(f"Самое длинное сообщение: {max(len(text) for text in texts)} символов")
        print(f"Самое короткое сообщение: {min(len(text) for text in texts)} символов")

        # Анализ слов
        all_words = []
        for text in texts:
            # Очищаем текст от ссылок и специальных символов
            clean_text = re.sub(r'http[s]?://\S+', '', text)
            clean_text = re.sub(r'[^\w\s]', ' ', clean_text)
            words = [word.lower() for word in clean_text.split() if len(word) > 2]
            all_words.extend(words)

        print(f"\n=== Анализ слов ===")
        print(f"Всего слов: {len(all_words):,}")
        print(f"Уникальных слов: {len(set(all_words)):,}")

        # Топ слов
        word_freq = Counter(all_words)
        top_words = word_freq.most_common(20)

        print(f"\n=== Топ-20 слов ===")
        for word, count in top_words:
            print(f"{word}: {count}")

        # Анализ тематики
        tech_words = ['технологии', 'ai', 'chatgpt', 'нейросеть', 'искусственный', 'интеллект', 'программирование', 'код', 'алгоритм', 'данные']
        tech_count = sum(word_freq.get(word, 0) for word in tech_words)

        business_words = ['деньги', 'доллар', 'стартап', 'бизнес', 'работа', 'компания', 'рынок']
        business_count = sum(word_freq.get(word, 0) for word in business_words)

        print(f"\n=== Тематический анализ ===")
        print(f"Технологические термины: {tech_count}")
        print(f"Бизнес термины: {business_count}")

        # Анализ ссылок
        links = []
        for text in texts:
            found_links = re.findall(r'http[s]?://\S+', text)
            links.extend(found_links)

        print(f"\n=== Анализ ссылок ===")
        print(f"Всего ссылок в сообщениях: {len(links)}")

        if links:
            domains = [re.findall(r'https?://([^/]+)', link)[0] for link in links if re.findall(r'https?://([^/]+)', link)]
            domain_count = Counter(domains)
            print("Топ доменов:")
            for domain, count in domain_count.most_common(10):
                print(f"  {domain}: {count}")

        # Анализ длины сообщений
        lengths = [len(text) for text in texts]
        short_messages = len([l for l in lengths if l < 100])
        medium_messages = len([l for l in lengths if 100 <= l < 500])
        long_messages = len([l for l in lengths if l >= 500])

        print(f"\n=== Распределение по длине ===")
        print(f"Короткие сообщения (<100 символов): {short_messages}")
        print(f"Средние сообщения (100-500 символов): {medium_messages}")
        print(f"Длинные сообщения (>500 символов): {long_messages}")

        # Создаем финальный отчет
        report = f"""# Полный анализ канала Denis Sexy IT 🤖

## Общая статистика
- **Всего сообщений:** {len(data)}
- **Сообщений для анализа:** {len(texts)}
- **Общее количество символов:** {total_chars:,}
- **Средняя длина сообщения:** {avg_length:.1f} символов

## Словарный анализ
- **Всего слов:** {len(all_words):,}
- **Уникальных слов:** {len(set(all_words)):,}
- **Словарное разнообразие:** {len(set(all_words))/len(all_words)*100:.1f}%

## Топ-20 самых частых слов
"""

        for word, count in top_words:
            report += f"- **{word}:** {count} раз\n"

        report += f"""
## Тематический анализ
- **Технологические термины:** {tech_count} упоминаний
- **Бизнес термины:** {business_count} упоминаний

## Анализ ссылок
- **Всего ссылок:** {len(links)}
"""

        if links:
            report += "\n### Топ доменов:\n"
            for domain, count in domain_count.most_common(5):
                report += f"- **{domain}:** {count} ссылок\n"

        report += f"""
## Распределение сообщений по длине
- **Короткие** (<100 символов): {short_messages} ({short_messages/len(texts)*100:.1f}%)
- **Средние** (100-500 символов): {medium_messages} ({medium_messages/len(texts)*100:.1f}%)
- **Длинные** (>500 символов): {long_messages} ({long_messages/len(texts)*100:.1f}%)

## Примеры характерных сообщений

### Самое длинное сообщение ({max(lengths)} символов):
```
{max(texts, key=len)[:500]}...
```

### Типичное сообщение средней длины:
```
{texts[len(texts)//2][:300]}...
```
"""

        # Сохраняем отчет
        with open('final_analysis_report.md', 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✅ Полный отчет сохранен в файл: final_analysis_report.md")

        return True

    except Exception as e:
        print(f"Ошибка при анализе: {e}")
        return False

if __name__ == "__main__":
    analyze_extracted_data()
