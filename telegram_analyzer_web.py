"""
Класс анализатора для веб-интерфейса
Поддерживает различные форматы дампов и создает структурированные отчеты
"""

import json
import re
from collections import Counter
from datetime import datetime
import pandas as pd
import numpy as np

class TelegramAnalyzer:
    def __init__(self):
        self.stop_words = self.get_russian_stop_words()

    def get_russian_stop_words(self):
        """Обновленный расширенный набор русских стоп-слов"""
        return {
            # Местоимения
            'я', 'мы', 'ты', 'вы', 'он', 'она', 'оно', 'они',
            'мой', 'моя', 'мое', 'мои', 'твой', 'твоя', 'твое', 'твои',
            'наш', 'наша', 'наше', 'наши', 'ваш', 'ваша', 'ваше', 'ваши',
            'его', 'ее', 'их', 'себя', 'себе', 'собой', 'собою', 'меня', 'тебя',

            # Указательные и вопросительные
            'этот', 'эта', 'это', 'эти', 'тот', 'та', 'то', 'те',
            'такой', 'такая', 'такое', 'такие', 'который', 'которая', 'которое', 'которые',
            'что', 'кто', 'где', 'когда', 'как', 'почему', 'зачем', 'откуда', 'куда',
            'сколько', 'какой', 'какая', 'какое', 'какие', 'чей', 'чья', 'чье', 'чьи',

            # Союзы и предлоги
            'и', 'а', 'но', 'или', 'либо', 'да', 'тоже', 'также', 'если', 'чтобы',
            'потому', 'поэтому', 'ведь', 'же', 'ли', 'бы', 'уже', 'еще', 'ещё',
            'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'об', 'при',
            'за', 'под', 'над', 'через', 'между', 'среди', 'без', 'около', 'возле',"так"

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
            'просто', 'только', 'пока', 'именно', 'конечно', 'наверное', 'возможно',
            'вообще', 'кстати', 'прочим', 'кроме', 'того', 'помимо', 'включая',
            'исключая', 'вам', 'нам', 'тем', 'более', 'менее', 'самый', 'самая',
            'самое', 'самые', 'лучше', 'хуже', 'больше', 'меньше', 'выше', 'ниже',

            # Технические слова (часто встречающиеся в телеграм)
            'https', 'http', 'www', 'com', 'ru', 'org', 'net', 't', 'me',
            'channel', 'chat', 'bot', 'forward', 'reply', 'edit'
        }

    def adapt_export_data(self, raw_data):
        """Адаптирует различные форматы экспорта под единый формат"""
        adapted_messages = []

        try:
            # Определяем тип экспорта
            if isinstance(raw_data, dict):
                if 'messages' in raw_data:
                    # Telegram Desktop экспорт
                    messages = raw_data['messages']
                    channel_info = {
                        'title': raw_data.get('name', 'Неизвестный канал'),
                        'type': raw_data.get('type', 'unknown'),
                        'id': raw_data.get('id')
                    }
                elif 'chats' in raw_data:
                    # Другой формат экспорта
                    messages = []
                    for chat in raw_data['chats'].get('list', []):
                        messages.extend(chat.get('messages', []))
                    channel_info = {'title': 'Мультичат экспорт', 'type': 'multiple'}
                else:
                    # Простой список сообщений
                    messages = raw_data if isinstance(raw_data, list) else [raw_data]
                    channel_info = {'title': 'Импортированные данные', 'type': 'unknown'}

            elif isinstance(raw_data, list):
                messages = raw_data
                channel_info = {'title': 'Список сообщений', 'type': 'list'}

            else:
                raise ValueError("Неподдерживаемый формат данных")

            # Обрабатываем сообщения
            for i, msg in enumerate(messages):
                try:
                    adapted_msg = self._adapt_message(msg, i)
                    if adapted_msg:
                        adapted_messages.append(adapted_msg)
                except Exception as e:
                    print(f"Ошибка обработки сообщения {i}: {e}")
                    continue

            return {
                'messages': adapted_messages,
                'channel_info': channel_info,
                'total_count': len(adapted_messages)
            }

        except Exception as e:
            raise Exception(f"Ошибка адаптации данных: {e}")

    def _adapt_message(self, msg, index):
        """Адаптирует отдельное сообщение под единый формат"""
        adapted = {
            'id': index,
            'date': None,
            'text': '',
            'from': None,
            'type': 'message'
        }

        # Извлекаем текст из различных форматов
        text_candidates = [
            msg.get('text', ''),
            msg.get('message', ''),
            msg.get('content', ''),
            msg.get('data_text', ''),
            str(msg) if isinstance(msg, str) else ''
        ]

        # Находим непустой текст
        for candidate in text_candidates:
            if candidate and len(str(candidate).strip()) > 0:
                if isinstance(candidate, list):
                    # Если текст представлен как список объектов (Telegram Desktop)
                    text_parts = []
                    for part in candidate:
                        if isinstance(part, dict):
                            text_parts.append(part.get('text', ''))
                        else:
                            text_parts.append(str(part))
                    adapted['text'] = ''.join(text_parts)
                else:
                    adapted['text'] = str(candidate)
                break

        # Извлекаем дату
        date_candidates = [
            msg.get('date'),
            msg.get('timestamp'),
            msg.get('created_at'),
            msg.get('data_time')
        ]

        for candidate in date_candidates:
            if candidate:
                adapted['date'] = str(candidate)
                break

        # Извлекаем автора
        from_candidates = [
            msg.get('from'),
            msg.get('author'),
            msg.get('sender'),
            msg.get('user')
        ]

        for candidate in from_candidates:
            if candidate:
                adapted['from'] = str(candidate)
                break

        # Фильтруем сообщения с пустым текстом
        if not adapted['text'] or len(adapted['text'].strip()) < 3:
            return None

        return adapted

    def clean_text(self, text):
        """Очищает текст от лишних символов и нормализует"""
        if not text:
            return ""

        # Убираем URL
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'www\.[^\s]+', '', text)

        # Убираем mentions и hashtags
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)

        # Убираем специальные символы, оставляем только буквы и цифры
        text = re.sub(r'[^\w\s]', ' ', text)

        # Нормализуем пробелы
        text = re.sub(r'\s+', ' ', text)

        return text.strip().lower()

    def extract_words(self, text):
        """Извлекает значимые слова из текста"""
        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return []

        words = cleaned_text.split()

        # Фильтруем слова
        filtered_words = []
        for word in words:
            if (len(word) >= 3 and
                word not in self.stop_words and
                not word.isdigit() and
                re.match(r'^[а-яё]+$', word)):
                filtered_words.append(word)

        return filtered_words

    def analyze_messages(self, adapted_data):
        """Основная функция анализа сообщений"""
        messages = adapted_data['messages']
        channel_info = adapted_data['channel_info']

        # Базовая статистика
        total_messages = len(messages)

        # Извлекаем тексты для анализа
        texts = [msg['text'] for msg in messages if msg['text']]

        # Анализ текста
        word_analysis = self._analyze_words(texts)
        message_stats = self._analyze_message_stats(texts)
        time_analysis = self._analyze_time_patterns(messages)

        # Формируем итоговый отчет
        report = {
            'total_messages': total_messages,
            'channel_info': channel_info,
            'word_analysis': word_analysis,
            'message_stats': message_stats,
            'time_analysis': time_analysis,
            'analysis_summary': self._create_summary(total_messages, word_analysis, message_stats)
        }

        return report

    def _analyze_words(self, texts):
        """Анализ слов и их частотности"""
        all_words = []

        for text in texts:
            words = self.extract_words(text)
            all_words.extend(words)

        word_counts = Counter(all_words)

        return {
            'total_words': len(all_words),
            'unique_words': len(word_counts),
            'top_words': word_counts.most_common(50),
            'vocabulary_richness': len(word_counts) / len(all_words) if all_words else 0
        }

    def _analyze_message_stats(self, texts):
        """Анализ статистики сообщений"""
        if not texts:
            return {}

        lengths = [len(text) for text in texts]

        return {
            'total_chars': sum(lengths),
            'average_length': np.mean(lengths),
            'median_length': np.median(lengths),
            'max_length': max(lengths),
            'min_length': min(lengths),
            'std_length': np.std(lengths)
        }

    def _analyze_time_patterns(self, messages):
        """Анализ временных паттернов"""
        dates = []
        hours = []

        for msg in messages:
            if msg.get('date'):
                try:
                    # Пытаемся парсить различные форматы дат
                    date_str = str(msg['date'])

                    # Telegram Desktop format
                    if 'T' in date_str:
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        # Пытаемся другие форматы
                        try:
                            dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
                        except:
                            continue

                    dates.append(dt.date())
                    hours.append(dt.hour)
                except:
                    continue

        if not dates:
            return {}

        # Анализ по часам
        hourly_dist = Counter(hours)

        # Анализ по датам
        date_dist = Counter(dates)

        # Находим самый активный час
        most_active_hour = hourly_dist.most_common(1)[0] if hourly_dist else (0, 0)

        return {
            'date_range': {
                'start_date': str(min(dates)),
                'end_date': str(max(dates)),
                'days': (max(dates) - min(dates)).days + 1
            },
            'hourly_distribution': dict(hourly_dist),
            'most_active_hour': most_active_hour[0],
            'most_active_hour_count': most_active_hour[1],
            'avg_messages_per_day': len(messages) / ((max(dates) - min(dates)).days + 1),
            'avg_messages_per_hour': len(messages) / 24
        }

    def _create_summary(self, total_messages, word_analysis, message_stats):
        """Создает краткое резюме анализа"""
        summary = []

        summary.append(f"Проанализировано {total_messages:,} сообщений")

        if word_analysis.get('total_words'):
            summary.append(f"Общее количество слов: {word_analysis['total_words']:,}")
            summary.append(f"Уникальных слов: {word_analysis['unique_words']:,}")
            summary.append(f"Богатство словаря: {word_analysis['vocabulary_richness']:.2%}")

        if message_stats.get('average_length'):
            summary.append(f"Средняя длина сообщения: {message_stats['average_length']:.1f} символов")

        return summary
