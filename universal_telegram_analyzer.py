"""
Обновленный анализатор для работы с новым форматом экспорта Telegram
Поддерживает как старый формат, так и новый экспорт Telegram Desktop
"""

import json
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from wordcloud import WordCloud
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# NLP библиотеки
import nltk
from nltk.corpus import stopwords
import pymorphy2

# Машинное обучение
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans

# Локальные модули
from telegram_export_adapter import TelegramExportAdapter

# Визуализация
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

class UniversalTelegramAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        self.processed_texts = []
        self.original_texts = []
        self.file_format = None  # 'old' или 'new'

        # Инициализация инструментов NLP
        self.morph = pymorphy2.MorphAnalyzer()

        # Загрузка стоп-слов
        try:
            self.stop_words = set(stopwords.words('russian'))
        except:
            nltk.download('stopwords')
            self.stop_words = set(stopwords.words('russian'))

        # Добавим дополнительные стоп-слова
        additional_stops = {
            'это', 'так', 'также', 'который', 'которые', 'которая', 'которое',
            'более', 'менее', 'очень', 'весьма', 'довольно', 'совсем',
            'тот', 'этот', 'этих', 'того', 'этого', 'тем', 'том',
            'вся', 'все', 'всех', 'всем', 'всему', 'всей',
            'один', 'одна', 'одно', 'одни', 'одних', 'одной',
            'канал', 'telegram', 'пост', 'сообщение', 'текст'
        }
        self.stop_words.update(additional_stops)

    def detect_format_and_load(self):
        """Автоматически определяет формат файла и загружает данные"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # Проверяем формат файла
        if isinstance(raw_data, list) and len(raw_data) > 0:
            # Старый формат - массив объектов с channel_id, message_id, data_text
            if 'channel_id' in raw_data[0] and 'data_text' in raw_data[0]:
                self.file_format = 'old'
                self.data = raw_data
                print("Обнаружен старый формат данных")
            else:
                raise ValueError("Неизвестный формат массива данных")

        elif isinstance(raw_data, dict) and 'messages' in raw_data:
            # Новый формат - объект с метаданными и массивом messages
            self.file_format = 'new'
            print("Обнаружен новый формат экспорта Telegram Desktop")

            # Используем адаптер для обработки
            adapter = TelegramExportAdapter(self.file_path)
            adapter.load_data()
            self.data = adapter.process_messages()

            # Выводим статистику адаптера
            stats = adapter.get_statistics()
            print(f"Обработано уникальных сообщений: {stats.get('total_processed', 0)}")
            print(f"Средняя длина текста: {stats.get('avg_text_length', 0):.1f} символов")

        else:
            raise ValueError("Неизвестный формат файла")

        # Извлекаем тексты
        self._extract_texts()

        return self.data

    def _extract_texts(self):
        """Извлекает тексты из загруженных данных"""
        self.original_texts = []

        for item in self.data:
            if 'data_text' in item and item['data_text']:
                text = item['data_text'].strip()
                if len(text) > 10:  # Минимальная длина для анализа
                    self.original_texts.append(text)

        print(f"Извлечено {len(self.original_texts)} текстов для анализа")

    def clean_text(self, text):
        """Очистка и предобработка текста"""
        # Удаляем markdown разметку
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)

        # Удаляем ссылки и упоминания
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r't\.me/\w+', '', text)

        # Удаляем эмодзи
        emoji_pattern = re.compile("["
                                 u"\U0001F600-\U0001F64F"  # emoticons
                                 u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                 u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                 u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                 u"\U00002702-\U000027B0"
                                 u"\U000024C2-\U0001F251"
                                 "]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)

        # Удаляем специальные символы и лишние пробелы
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.lower().strip()

    def tokenize_and_lemmatize(self, text):
        """Токенизация и лемматизация текста"""
        # Удаляем цифры
        text = re.sub(r'\d+', '', text)

        # Токенизация
        tokens = text.split()

        # Фильтрация и лемматизация
        processed_tokens = []
        for token in tokens:
            if len(token) > 2 and token not in self.stop_words:
                # Лемматизация
                try:
                    parsed = self.morph.parse(token)[0]
                    lemma = parsed.normal_form

                    # Дополнительная фильтрация
                    if lemma not in self.stop_words and len(lemma) > 2:
                        processed_tokens.append(lemma)
                except:
                    # Если лемматизация не удалась, используем исходное слово
                    if len(token) > 2:
                        processed_tokens.append(token)

        return processed_tokens

    def preprocess_texts(self):
        """Предобработка всех текстов"""
        print("Начинаем предобработку текстов...")

        for i, text in enumerate(self.original_texts):
            # Очистка
            cleaned = self.clean_text(text)

            # Токенизация и лемматизация
            tokens = self.tokenize_and_lemmatize(cleaned)

            # Сохраняем обработанный текст
            if tokens:
                self.processed_texts.append(' '.join(tokens))

            if (i + 1) % 100 == 0:
                print(f"Обработано {i + 1}/{len(self.original_texts)} текстов")

        print(f"Предобработка завершена. Получено {len(self.processed_texts)} обработанных текстов")

    def get_word_frequency(self, top_n=30):
        """Анализ частотности слов"""
        if not self.processed_texts:
            self.preprocess_texts()

        # Объединяем все тексты
        all_words = []
        for text in self.processed_texts:
            all_words.extend(text.split())

        # Подсчитываем частоты
        word_freq = Counter(all_words)

        return word_freq.most_common(top_n)

    def create_wordcloud(self, save_path=None):
        """Создание облака слов"""
        if not self.processed_texts:
            self.preprocess_texts()

        # Объединяем все тексты
        all_text = ' '.join(self.processed_texts)

        if not all_text.strip():
            print("Нет текста для создания облака слов")
            return None

        # Создаем облако слов
        wordcloud = WordCloud(
            width=1200,
            height=600,
            background_color='white',
            max_words=100,
            colormap='viridis',
            font_path=None  # Используем стандартный шрифт
        ).generate(all_text)

        # Визуализация
        plt.figure(figsize=(15, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Облако слов канала', fontsize=16, pad=20)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Облако слов сохранено: {save_path}")

        plt.show()
        return wordcloud

    def analyze_topics(self, n_topics=5):
        """Тематическое моделирование"""
        if not self.processed_texts:
            self.preprocess_texts()

        if len(self.processed_texts) < n_topics:
            print(f"Недостаточно текстов для анализа {n_topics} тем")
            return None

        # Векторизация
        vectorizer = TfidfVectorizer(
            max_features=1000,
            min_df=2,
            max_df=0.8,
            ngram_range=(1, 2)
        )

        try:
            doc_term_matrix = vectorizer.fit_transform(self.processed_texts)

            # LDA
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                max_iter=100
            )

            lda.fit(doc_term_matrix)

            # Извлекаем темы
            feature_names = vectorizer.get_feature_names_out()
            topics = []

            for topic_idx, topic in enumerate(lda.components_):
                top_words = [feature_names[i] for i in topic.argsort()[-10:][::-1]]
                topics.append({
                    'topic_id': topic_idx,
                    'words': top_words,
                    'weights': sorted(topic, reverse=True)[:10]
                })

            return topics

        except Exception as e:
            print(f"Ошибка при анализе тем: {e}")
            return None

    def get_time_analysis(self):
        """Анализ временной активности"""
        if not self.data:
            return None

        dates = []
        for item in self.data:
            if 'date' in item and item['date']:
                try:
                    # Пробуем разные форматы дат
                    date_str = item['date']
                    if 'T' in date_str:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', ''))
                    else:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    dates.append(date_obj)
                except:
                    # Пробуем unix timestamp
                    if 'date_unixtime' in item:
                        try:
                            date_obj = datetime.fromtimestamp(int(item['date_unixtime']))
                            dates.append(date_obj)
                        except:
                            pass

        if not dates:
            return None

        # Анализ по месяцам
        df = pd.DataFrame({'date': dates})
        df['year_month'] = df['date'].dt.to_period('M')
        df['hour'] = df['date'].dt.hour
        df['weekday'] = df['date'].dt.weekday

        monthly_counts = df['year_month'].value_counts().sort_index()
        hourly_counts = df['hour'].value_counts().sort_index()
        weekday_counts = df['weekday'].value_counts().sort_index()

        return {
            'monthly': monthly_counts,
            'hourly': hourly_counts,
            'weekday': weekday_counts,
            'total_days': (max(dates) - min(dates)).days,
            'first_message': min(dates),
            'last_message': max(dates)
        }

    def generate_report(self, output_file=None):
        """Генерация полного отчета"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"telegram_analysis_report_{timestamp}.md"

        # Собираем данные для отчета
        word_freq = self.get_word_frequency(20)
        topics = self.analyze_topics(5)
        time_analysis = self.get_time_analysis()

        # Формируем отчет
        report = f"""# Анализ Telegram канала

## Общая информация
- Формат данных: {self.file_format}
- Всего сообщений в данных: {len(self.data) if self.data else 0}
- Сообщений для анализа: {len(self.original_texts)}
- Обработанных текстов: {len(self.processed_texts)}

## Частотный анализ слов
"""

        if word_freq:
            report += "| Слово | Частота |\n|-------|--------|\n"
            for word, freq in word_freq:
                report += f"| {word} | {freq} |\n"

        if topics:
            report += "\n## Тематический анализ\n"
            for i, topic in enumerate(topics, 1):
                words = ', '.join(topic['words'][:5])
                report += f"**Тема {i}:** {words}\n\n"

        if time_analysis:
            report += f"\n## Временной анализ\n"
            report += f"- Период: {time_analysis['first_message'].strftime('%Y-%m-%d')} - {time_analysis['last_message'].strftime('%Y-%m-%d')}\n"
            report += f"- Общий период: {time_analysis['total_days']} дней\n"
            report += f"- Среднее сообщений в месяц: {len(self.original_texts) / max(1, time_analysis['total_days'] / 30.4):.1f}\n"

        # Сохраняем отчет
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"Отчет сохранен: {output_file}")
        return output_file

# Пример использования
if __name__ == "__main__":
    analyzer = UniversalTelegramAnalyzer("result.json")
    analyzer.detect_format_and_load()
    analyzer.generate_report()
