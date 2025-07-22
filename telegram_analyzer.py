"""
Комплексный анализатор сообщений Telegram канала
Включает: предобработку текста, тематическое моделирование, анализ тональности, частотный анализ
"""

import json
import re
import string
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from wordcloud import WordCloud
import warnings
warnings.filterwarnings('ignore')

# NLP библиотеки
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
import pymorphy2

# Машинное обучение
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans

# Анализ тональности
from textblob import TextBlob
from dostoevsky.tokenization import RegexTokenizer
from dostoevsky.models import FastTextSocialNetworkModel

# Визуализация
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

class TelegramAnalyzer:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.data = None
        self.processed_texts = []
        self.original_texts = []

        # Инициализация инструментов NLP
        self.morph = pymorphy2.MorphAnalyzer()
        self.stemmer = SnowballStemmer("russian")

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
            'один', 'одна', 'одно', 'одни', 'одних', 'одной'
        }
        self.stop_words.update(additional_stops)

        # Инициализация модели тональности
        try:
            self.tokenizer = RegexTokenizer()
            self.sentiment_model = FastTextSocialNetworkModel(tokenizer=self.tokenizer)
        except:
            print("Модель тональности недоступна, будет использован альтернативный метод")
            self.sentiment_model = None

    def load_data(self):
        """Загрузка данных из JSON файла"""
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        # Извлекаем тексты сообщений
        for item in self.data:
            if 'data_text' in item and item['data_text']:
                self.original_texts.append(item['data_text'])

        print(f"Загружено {len(self.original_texts)} сообщений")
        return self.data

    def clean_text(self, text):
        """Очистка и предобработка текста"""
        # Удаляем markdown разметку
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)

        # Удаляем ссылки
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

        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        # Приводим к нижнему регистру
        text = text.lower().strip()

        return text

    def tokenize_and_lemmatize(self, text):
        """Токенизация и лемматизация текста"""
        # Удаляем пунктуацию и цифры
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)

        # Токенизация
        tokens = text.split()

        # Фильтрация и лемматизация
        processed_tokens = []
        for token in tokens:
            if len(token) > 2 and token not in self.stop_words:
                # Лемматизация
                parsed = self.morph.parse(token)[0]
                lemma = parsed.normal_form

                # Дополнительная фильтрация
                if lemma not in self.stop_words and len(lemma) > 2:
                    processed_tokens.append(lemma)

        return processed_tokens

    def preprocess_texts(self):
        """Предобработка всех текстов"""
        print("Начинаем предобработку текстов...")

        for i, text in enumerate(self.original_texts):
            # Очистка
            cleaned = self.clean_text(text)

            # Токенизация и лемматизация
            tokens = self.tokenize_and_lemmatize(cleaned)

            # Объединяем обратно в текст
            processed_text = ' '.join(tokens)
            self.processed_texts.append(processed_text)

            if (i + 1) % 100 == 0:
                print(f"Обработано {i + 1} текстов...")

        print(f"Предобработка завершена. Обработано {len(self.processed_texts)} текстов")
        return self.processed_texts

    def frequency_analysis(self, top_n=30):
        """Частотный анализ слов"""
        print("Проводим частотный анализ...")

        # Объединяем все обработанные тексты
        all_words = []
        for text in self.processed_texts:
            all_words.extend(text.split())

        # Подсчет частот
        word_freq = Counter(all_words)
        most_common = word_freq.most_common(top_n)

        # Создание DataFrame для удобства
        freq_df = pd.DataFrame(most_common, columns=['word', 'frequency'])

        # Визуализация
        plt.figure(figsize=(15, 8))
        plt.subplot(1, 2, 1)
        words, freqs = zip(*most_common)
        plt.barh(range(len(words)), freqs)
        plt.yticks(range(len(words)), words)
        plt.xlabel('Частота')
        plt.title(f'Топ-{top_n} наиболее частых слов')
        plt.gca().invert_yaxis()

        # Облако слов
        plt.subplot(1, 2, 2)
        wordcloud = WordCloud(width=800, height=600,
                            background_color='white',
                            font_path='arial.ttf',
                            max_words=100).generate_from_frequencies(dict(most_common))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Облако слов')

        plt.tight_layout()
        plt.savefig('frequency_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()

        return freq_df

    def topic_modeling(self, n_topics=5):
        """Тематическое моделирование с использованием LDA"""
        print("Проводим тематическое моделирование...")

        # Подготовка данных для LDA
        vectorizer = TfidfVectorizer(
            max_features=1000,
            min_df=2,
            max_df=0.8,
            ngram_range=(1, 2)
        )

        tfidf_matrix = vectorizer.fit_transform(self.processed_texts)
        feature_names = vectorizer.get_feature_names_out()

        # LDA модель
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=100
        )

        lda.fit(tfidf_matrix)

        # Извлечение тем
        topics = []
        for topic_idx, topic in enumerate(lda.components_):
            top_words_idx = topic.argsort()[-10:][::-1]
            top_words = [feature_names[i] for i in top_words_idx]
            top_weights = [topic[i] for i in top_words_idx]
            topics.append({
                'topic_id': topic_idx,
                'words': top_words,
                'weights': top_weights
            })

        # Визуализация тем
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()

        for i, topic in enumerate(topics):
            if i < len(axes):
                ax = axes[i]
                words = topic['words'][:8]
                weights = topic['weights'][:8]

                ax.barh(range(len(words)), weights)
                ax.set_yticks(range(len(words)))
                ax.set_yticklabels(words)
                ax.set_title(f'Тема {i+1}')
                ax.invert_yaxis()

        # Убираем лишние подграфики
        for i in range(len(topics), len(axes)):
            axes[i].remove()

        plt.tight_layout()
        plt.savefig('topic_modeling.png', dpi=300, bbox_inches='tight')
        plt.show()

        return topics, lda, vectorizer

    def sentiment_analysis(self):
        """Анализ тональности текстов"""
        print("Проводим анализ тональности...")

        sentiments = []

        for text in self.original_texts:
            if self.sentiment_model:
                # Используем dostoevsky для русского языка
                try:
                    result = self.sentiment_model.predict([text])[0]
                    # Преобразуем в более простую схему
                    if result['positive'] > result['negative']:
                        sentiment = 'positive'
                        confidence = result['positive']
                    elif result['negative'] > result['positive']:
                        sentiment = 'negative'
                        confidence = result['negative']
                    else:
                        sentiment = 'neutral'
                        confidence = result['neutral']
                except:
                    sentiment = 'neutral'
                    confidence = 0.5
            else:
                # Альтернативный метод через TextBlob
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                if polarity > 0.1:
                    sentiment = 'positive'
                elif polarity < -0.1:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
                confidence = abs(polarity)

            sentiments.append({
                'text': text[:100] + '...' if len(text) > 100 else text,
                'sentiment': sentiment,
                'confidence': confidence
            })

        # Создание DataFrame
        sentiment_df = pd.DataFrame(sentiments)

        # Подсчет статистики
        sentiment_counts = sentiment_df['sentiment'].value_counts()

        # Визуализация
        plt.figure(figsize=(15, 6))

        plt.subplot(1, 2, 1)
        plt.pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%')
        plt.title('Распределение тональности сообщений')

        plt.subplot(1, 2, 2)
        sentiment_counts.plot(kind='bar')
        plt.title('Количество сообщений по тональности')
        plt.xlabel('Тональность')
        plt.ylabel('Количество')
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig('sentiment_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()

        return sentiment_df, sentiment_counts

    def generate_report_data(self):
        """Подготовка данных для отчета LLM"""
        print("Подготавливаем данные для отчета...")

        # Общая статистика
        total_messages = len(self.original_texts)
        avg_message_length = np.mean([len(text) for text in self.original_texts])

        # Частотный анализ
        freq_df = self.frequency_analysis(top_n=20)

        # Тематическое моделирование
        topics, lda_model, vectorizer = self.topic_modeling(n_topics=5)

        # Анализ тональности
        sentiment_df, sentiment_counts = self.sentiment_analysis()

        # Формируем данные для отчета
        report_data = {
            'general_stats': {
                'total_messages': total_messages,
                'average_message_length': avg_message_length,
                'total_words_processed': len(' '.join(self.processed_texts).split())
            },
            'top_words': freq_df.head(15).to_dict('records'),
            'topics': topics,
            'sentiment_distribution': sentiment_counts.to_dict(),
            'sentiment_percentage': (sentiment_counts / total_messages * 100).to_dict(),
            'sample_messages': {
                'positive': [],
                'negative': [],
                'neutral': []
            }
        }

        # Добавляем примеры сообщений для каждой тональности
        for sentiment_type in ['positive', 'negative', 'neutral']:
            samples = sentiment_df[sentiment_df['sentiment'] == sentiment_type].head(3)
            report_data['sample_messages'][sentiment_type] = samples['text'].tolist()

        # Сохраняем в JSON для передачи в LLM
        with open('analysis_report_data.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print("Данные для отчета сохранены в 'analysis_report_data.json'")
        return report_data

def main():
    # Инициализация анализатора
    analyzer = TelegramAnalyzer('parsed_data_20250722_114557.json')

    # Загрузка данных
    analyzer.load_data()

    # Предобработка текстов
    analyzer.preprocess_texts()

    # Генерация отчета
    report_data = analyzer.generate_report_data()

    print("\nАнализ завершен!")
    print("Созданы следующие файлы:")
    print("- frequency_analysis.png - частотный анализ")
    print("- topic_modeling.png - тематическое моделирование")
    print("- sentiment_analysis.png - анализ тональности")
    print("- analysis_report_data.json - данные для LLM отчета")

    return analyzer, report_data

if __name__ == "__main__":
    analyzer, report_data = main()
