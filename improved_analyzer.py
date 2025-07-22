"""
Улучшенный финальный анализатор с расширенным словарем стоп-слов
"""

import json
import re
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

def get_russian_stop_words():
    """Расширенный набор русских стоп-слов"""
    return {
        # Местоимения
        'я', 'мы', 'ты', 'вы', 'он', 'она', 'оно', 'они',
        'мой', 'моя', 'мое', 'мои', 'твой', 'твоя', 'твое', 'твои',
        'наш', 'наша', 'наше', 'наши', 'ваш', 'ваша', 'ваше', 'ваши',
        'его', 'ее', 'их', 'себя', 'себе', 'собой', 'собою',

        # Указательные и вопросительные
        'этот', 'эта', 'это', 'эти', 'тот', 'та', 'то', 'те',
        'такой', 'такая', 'такое', 'такие', 'который', 'которая', 'которое', 'которые',
        'что', 'кто', 'где', 'когда', 'как', 'почему', 'зачем', 'откуда', 'куда',
        'сколько', 'какой', 'какая', 'какое', 'какие', 'чей', 'чья', 'чье', 'чьи',

        # Союзы и предлоги
        'и', 'а', 'но', 'или', 'либо', 'да', 'тоже', 'также', 'если', 'чтобы',
        'что', 'как', 'потому', 'поэтому', 'ведь', 'же', 'ли', 'бы', 'уже',
        'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'об', 'при',
        'за', 'под', 'над', 'через', 'между', 'среди', 'без', 'около', 'возле',

        # Частицы и наречия
        'не', 'ни', 'вот', 'вон', 'да', 'нет', 'тут', 'там', 'здесь', 'сюда',
        'туда', 'отсюда', 'оттуда', 'везде', 'всюду', 'нигде', 'никуда',
        'очень', 'весьма', 'довольно', 'совсем', 'почти', 'слишком', 'едва',
        'вдруг', 'сейчас', 'теперь', 'потом', 'тогда', 'всегда', 'никогда',
        'иногда', 'часто', 'редко', 'рано', 'поздно', 'давно', 'недавно',

        # Количественные
        'один', 'одна', 'одно', 'одни', 'два', 'две', 'три', 'четыре', 'пять',
        'много', 'мало', 'несколько', 'все', 'всё', 'всех', 'всем', 'всему',
        'каждый', 'каждая', 'каждое', 'любой', 'любая', 'любое', 'другой',

        # Вспомогательные слова
        'быть', 'есть', 'был', 'была', 'было', 'были', 'буду', 'будешь', 'будет',
        'будем', 'будете', 'будут', 'бывать', 'стать', 'стал', 'стала', 'стало', 'стали',
        'мочь', 'могу', 'можешь', 'может', 'можем', 'можете', 'могут', 'мог', 'могла',
        'хотеть', 'хочу', 'хочешь', 'хочет', 'хотим', 'хотите', 'хотят', 'хотел',

        # Общие слова
        'так', 'более', 'менее', 'лучше', 'хуже', 'больше', 'меньше', 'раз',
        'год', 'день', 'время', 'человек', 'люди', 'дело', 'вещь', 'место',
        'работа', 'жизнь', 'дом', 'рука', 'нога', 'голова', 'глаз', 'слово',

        # Telegram специфичные
        'канал', 'telegram', 'пост', 'сообщение', 'текст', 'ссылка', 'видео',
        'фото', 'картинка', 'файл', 'документ', 'голосовое', 'стикер',

        # Эмоциональные и оценочные
        'хорошо', 'плохо', 'отлично', 'ужасно', 'нормально', 'классно', 'круто',
        'интересно', 'скучно', 'важно', 'нужно', 'можно', 'нельзя', 'должен',

        # Дополнительные частые слова
        'просто', 'только', 'еще', 'ещё', 'уже', 'пока', 'именно', 'конечно',
        'наверное', 'возможно', 'вообще', 'кстати', 'между', 'прочим', 'кроме',
        'того', 'помимо', 'включая', 'исключая', 'мне', 'вам', 'нам', 'тем'
    }

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

        # Улучшенный анализ слов с расширенными стоп-словами
        stop_words = get_russian_stop_words()
        all_words = []

        for text in texts:
            # Очищаем текст от ссылок и специальных символов
            clean_text = re.sub(r'http[s]?://\S+', '', text)
            clean_text = re.sub(r'@\w+', '', clean_text)  # убираем упоминания
            clean_text = re.sub(r'[^\w\s]', ' ', clean_text)
            clean_text = re.sub(r'\d+', ' ', clean_text)  # убираем цифры

            words = [word.lower().strip() for word in clean_text.split()
                    if len(word) > 2 and word.lower() not in stop_words]
            all_words.extend(words)

        print(f"\n=== Анализ слов ===")
        print(f"Всего слов: {len(all_words):,}")
        print(f"Уникальных слов: {len(set(all_words)):,}")

        # Топ слов
        word_freq = Counter(all_words)
        top_words = word_freq.most_common(25)

        print(f"\n=== Топ-25 значимых слов ===")
        for word, count in top_words:
            print(f"{word}: {count}")

        # Анализ тематики
        tech_words = ['технологии', 'технология', 'chatgpt', 'нейросеть', 'нейросети',
                     'искусственный', 'интеллект', 'программирование', 'код', 'алгоритм',
                     'данные', 'разработка', 'софт', 'программа', 'api', 'модель',
                     'openai', 'anthropic', 'google', 'deepmind', 'microsoft']
        tech_count = sum(word_freq.get(word, 0) for word in tech_words)

        business_words = ['деньги', 'доллар', 'доллары', 'стартап', 'бизнес', 'работа',
                         'компания', 'рынок', 'продажи', 'клиент', 'клиенты', 'цена',
                         'стоимость', 'инвестиции', 'прибыль', 'капитал', 'экономика']
        business_count = sum(word_freq.get(word, 0) for word in business_words)

        science_words = ['исследование', 'исследования', 'наука', 'ученые', 'открытие',
                        'эксперимент', 'результат', 'анализ', 'статья', 'публикация',
                        'arxiv', 'paper', 'study']
        science_count = sum(word_freq.get(word, 0) for word in science_words)

        print(f"\n=== Тематический анализ ===")
        print(f"Технологические термины: {tech_count}")
        print(f"Бизнес термины: {business_count}")
        print(f"Научные термины: {science_count}")

        # Анализ ссылок
        links = []
        for text in texts:
            found_links = re.findall(r'http[s]?://\S+', text)
            links.extend(found_links)

        print(f"\n=== Анализ ссылок ===")
        print(f"Всего ссылок в сообщениях: {len(links)}")

        domain_count = Counter()
        if links:
            domains = []
            for link in links:
                domain_match = re.findall(r'https?://([^/]+)', link)
                if domain_match:
                    domains.append(domain_match[0])
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

        # Создаем финальный отчет без примеров сообщений
        report = f"""# 📊 Анализ канала Denis Sexy IT 🤖

## 📈 Общая статистика
- **Всего сообщений:** {len(data)}
- **Сообщений для анализа:** {len(texts)}
- **Общее количество символов:** {total_chars:,}
- **Средняя длина сообщения:** {avg_length:.1f} символов

## 📝 Словарный анализ
- **Всего слов:** {len(all_words):,}
- **Уникальных слов:** {len(set(all_words)):,}
- **Словарное разнообразие:** {len(set(all_words))/len(all_words)*100:.1f}%

## 🔥 Топ-25 значимых слов
"""

        for i, (word, count) in enumerate(top_words, 1):
            report += f"{i}. **{word}** — {count} раз\n"

        report += f"""
## 🎯 Тематический анализ
- **🤖 Технологические термины:** {tech_count} упоминаний
- **💼 Бизнес термины:** {business_count} упоминаний  
- **🔬 Научные термины:** {science_count} упоминаний

## 🔗 Анализ ссылок
- **Всего ссылок:** {len(links)}
"""

        if links:
            report += "\n### 🌐 Топ-10 доменов:\n"
            for i, (domain, count) in enumerate(domain_count.most_common(10), 1):
                report += f"{i}. **{domain}** — {count} ссылок\n"

        report += f"""
## 📏 Распределение сообщений по длине
- **📝 Короткие** (<100 символов): {short_messages} ({short_messages/len(texts)*100:.1f}%)
- **📄 Средние** (100-500 символов): {medium_messages} ({medium_messages/len(texts)*100:.1f}%)
- **📖 Длинные** (>500 символов): {long_messages} ({long_messages/len(texts)*100:.1f}%)

## 💡 Выводы
- Канал фокусируется на **IT и технологиях** ({tech_count} упоминаний)
- Активно используются **внешние ссылки** ({len(links)} штук)
- Преобладают **развернутые посты** ({(medium_messages + long_messages)/len(texts)*100:.1f}% средних и длинных)
- Высокое **словарное разнообразие** ({len(set(all_words))/len(all_words)*100:.1f}%)

---
*Отчет создан: {datetime.now().strftime('%d.%m.%Y %H:%M')}*
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
