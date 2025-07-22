"""
Расширенная визуализация и анализ данных Telegram канала
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import re
from collections import Counter, defaultdict
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
from sklearn.cluster import DBSCAN

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

class AdvancedAnalyzer:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.data = None
        self.df = None

    def load_data(self):
        """Загрузка и подготовка данных"""
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        # Создаем DataFrame
        self.df = pd.DataFrame(self.data)
        self.df['text_length'] = self.df['data_text'].str.len()
        self.df['word_count'] = self.df['data_text'].str.split().str.len()

        return self.df

    def analyze_message_patterns(self):
        """Анализ паттернов сообщений"""
        print("Анализируем паттерны сообщений...")

        # Анализ длины сообщений
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # Распределение длины сообщений
        axes[0, 0].hist(self.df['text_length'], bins=30, alpha=0.7, color='skyblue')
        axes[0, 0].set_title('Распределение длины сообщений (символы)')
        axes[0, 0].set_xlabel('Длина сообщения')
        axes[0, 0].set_ylabel('Частота')

        # Распределение количества слов
        axes[0, 1].hist(self.df['word_count'], bins=30, alpha=0.7, color='lightgreen')
        axes[0, 1].set_title('Распределение количества слов')
        axes[0, 1].set_xlabel('Количество слов')
        axes[0, 1].set_ylabel('Частота')

        # Boxplot длины сообщений
        axes[1, 0].boxplot(self.df['text_length'])
        axes[1, 0].set_title('Boxplot длины сообщений')
        axes[1, 0].set_ylabel('Длина сообщения')

        # Соотношение символов и слов
        axes[1, 1].scatter(self.df['word_count'], self.df['text_length'], alpha=0.6)
        axes[1, 1].set_title('Соотношение слов и символов')
        axes[1, 1].set_xlabel('Количество слов')
        axes[1, 1].set_ylabel('Количество символов')

        plt.tight_layout()
        plt.savefig('message_patterns.png', dpi=300, bbox_inches='tight')
        plt.show()

        # Статистика
        stats = {
            'avg_length': self.df['text_length'].mean(),
            'median_length': self.df['text_length'].median(),
            'avg_words': self.df['word_count'].mean(),
            'median_words': self.df['word_count'].median(),
            'longest_message': self.df['text_length'].max(),
            'shortest_message': self.df['text_length'].min()
        }

        return stats

    def analyze_linguistic_features(self):
        """Анализ лингвистических особенностей"""
        print("Анализируем лингвистические особенности...")

        # Анализ знаков препинания и эмодзи
        punctuation_counts = []
        emoji_counts = []
        caps_counts = []

        emoji_pattern = re.compile("["
                                 u"\U0001F600-\U0001F64F"  # emoticons
                                 u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                 u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                 u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                 u"\U00002702-\U000027B0"
                                 u"\U000024C2-\U0001F251"
                                 "]+", flags=re.UNICODE)

        for text in self.df['data_text']:
            # Подсчет знаков препинания
            punct_count = len(re.findall(r'[!?.,;:]', text))
            punctuation_counts.append(punct_count)

            # Подсчет эмодзи
            emoji_count = len(emoji_pattern.findall(text))
            emoji_counts.append(emoji_count)

            # Подсчет заглавных букв
            caps_count = sum(1 for c in text if c.isupper())
            caps_counts.append(caps_count)

        self.df['punctuation_count'] = punctuation_counts
        self.df['emoji_count'] = emoji_counts
        self.df['caps_count'] = caps_counts

        # Визуализация
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        axes[0, 0].hist(self.df['punctuation_count'], bins=20, alpha=0.7, color='orange')
        axes[0, 0].set_title('Распределение знаков препинания')
        axes[0, 0].set_xlabel('Количество знаков препинания')

        axes[0, 1].hist(self.df['emoji_count'], bins=15, alpha=0.7, color='pink')
        axes[0, 1].set_title('Распределение эмодзи')
        axes[0, 1].set_xlabel('Количество эмодзи')

        axes[1, 0].hist(self.df['caps_count'], bins=20, alpha=0.7, color='red')
        axes[1, 0].set_title('Распределение заглавных букв')
        axes[1, 0].set_xlabel('Количество заглавных букв')

        # Корреляция между признаками
        corr_data = self.df[['text_length', 'word_count', 'punctuation_count', 'emoji_count', 'caps_count']].corr()
        sns.heatmap(corr_data, annot=True, cmap='coolwarm', center=0, ax=axes[1, 1])
        axes[1, 1].set_title('Корреляция лингвистических признаков')

        plt.tight_layout()
        plt.savefig('linguistic_features.png', dpi=300, bbox_inches='tight')
        plt.show()

        return {
            'avg_punctuation': np.mean(punctuation_counts),
            'avg_emoji': np.mean(emoji_counts),
            'avg_caps': np.mean(caps_counts)
        }

    def find_key_phrases(self, n_grams=2, top_n=20):
        """Поиск ключевых фраз и n-грамм"""
        print("Ищем ключевые фразы...")

        from sklearn.feature_extraction.text import TfidfVectorizer

        # Очистка текстов для n-грамм
        cleaned_texts = []
        for text in self.df['data_text']:
            # Удаляем markdown и ссылки
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'__([^_]+)__', r'\1', text)
            text = re.sub(r'http[s]?://\S+', '', text)
            text = re.sub(r'@\w+', '', text)
            text = text.lower()
            cleaned_texts.append(text)

        # Извлечение n-грамм
        vectorizer = TfidfVectorizer(
            ngram_range=(n_grams, n_grams),
            max_features=100,
            min_df=2,
            max_df=0.8,
            stop_words=None
        )

        tfidf_matrix = vectorizer.fit_transform(cleaned_texts)
        feature_names = vectorizer.get_feature_names_out()

        # Получение средних TF-IDF значений
        mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)

        # Топ n-грамм
        top_indices = mean_scores.argsort()[-top_n:][::-1]
        top_ngrams = [(feature_names[i], mean_scores[i]) for i in top_indices]

        # Визуализация
        plt.figure(figsize=(12, 8))
        phrases, scores = zip(*top_ngrams)
        plt.barh(range(len(phrases)), scores)
        plt.yticks(range(len(phrases)), phrases)
        plt.xlabel('TF-IDF Score')
        plt.title(f'Топ-{top_n} ключевых {n_grams}-грамм')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(f'key_phrases_{n_grams}grams.png', dpi=300, bbox_inches='tight')
        plt.show()

        return top_ngrams

    def analyze_semantic_similarity(self):
        """Анализ семантической близости сообщений"""
        print("Анализируем семантическую близость...")

        # Векторизация текстов
        vectorizer = TfidfVectorizer(max_features=500, min_df=2, max_df=0.8)
        tfidf_matrix = vectorizer.fit_transform(self.df['data_text'])

        # Матрица схожести
        similarity_matrix = cosine_similarity(tfidf_matrix)

        # t-SNE для визуализации
        if len(self.df) > 50:  # t-SNE только для достаточного количества документов
            tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(self.df)-1))
            tsne_results = tsne.fit_transform(tfidf_matrix.toarray())

            plt.figure(figsize=(12, 8))
            plt.scatter(tsne_results[:, 0], tsne_results[:, 1], alpha=0.6)
            plt.title('t-SNE визуализация сообщений')
            plt.xlabel('t-SNE 1')
            plt.ylabel('t-SNE 2')

            # Добавляем номера сообщений
            for i, (x, y) in enumerate(tsne_results):
                if i % 5 == 0:  # Показываем каждое 5-е сообщение
                    plt.annotate(str(i), (x, y), fontsize=8, alpha=0.7)

            plt.tight_layout()
            plt.savefig('semantic_similarity.png', dpi=300, bbox_inches='tight')
            plt.show()

        # Кластеризация сообщений
        if len(self.df) > 10:
            dbscan = DBSCAN(metric='cosine', eps=0.3, min_samples=2)
            clusters = dbscan.fit_predict(tfidf_matrix.toarray())

            cluster_info = pd.Series(clusters).value_counts()
            print(f"Найдено кластеров: {len(cluster_info[cluster_info.index != -1])}")
            print(f"Сообщений вне кластеров: {cluster_info.get(-1, 0)}")

            return clusters

        return None

    def create_comprehensive_report(self):
        """Создание расширенного отчета с визуализациями"""
        print("Создаем расширенный отчет...")

        # Загружаем данные
        self.load_data()

        # Проводим все анализы
        message_stats = self.analyze_message_patterns()
        linguistic_stats = self.analyze_linguistic_features()
        key_phrases_2gram = self.find_key_phrases(n_grams=2, top_n=15)
        key_phrases_3gram = self.find_key_phrases(n_grams=3, top_n=10)
        clusters = self.analyze_semantic_similarity()

        # Формируем отчет
        report = f"""
# РАСШИРЕННЫЙ АНАЛИЗ TELEGRAM КАНАЛА
Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}

## СТАТИСТИКА СООБЩЕНИЙ
- Среднее количество символов: {message_stats['avg_length']:.1f}
- Медиана символов: {message_stats['median_length']:.1f}
- Среднее количество слов: {message_stats['avg_words']:.1f}
- Медиана слов: {message_stats['median_words']:.1f}
- Самое длинное сообщение: {message_stats['longest_message']} символов
- Самое короткое сообщение: {message_stats['shortest_message']} символов

## ЛИНГВИСТИЧЕСКИЕ ОСОБЕННОСТИ
- Среднее количество знаков препинания: {linguistic_stats['avg_punctuation']:.1f}
- Среднее количество эмодзи: {linguistic_stats['avg_emoji']:.1f}
- Среднее количество заглавных букв: {linguistic_stats['avg_caps']:.1f}

## КЛЮЧЕВЫЕ БИГРАММЫ (2-граммы)
"""
        for i, (phrase, score) in enumerate(key_phrases_2gram[:10], 1):
            report += f"{i}. {phrase} (TF-IDF: {score:.3f})\n"

        report += "\n## КЛЮЧЕВЫЕ ТРИГРАММЫ (3-граммы)\n"
        for i, (phrase, score) in enumerate(key_phrases_3gram[:8], 1):
            report += f"{i}. {phrase} (TF-IDF: {score:.3f})\n"

        if clusters is not None:
            cluster_counts = pd.Series(clusters).value_counts()
            report += f"\n## КЛАСТЕРНЫЙ АНАЛИЗ\n"
            report += f"- Количество выявленных кластеров: {len(cluster_counts[cluster_counts.index != -1])}\n"
            report += f"- Сообщений в кластерах: {len(clusters[clusters != -1])}\n"
            report += f"- Сообщений вне кластеров: {sum(clusters == -1)}\n"

        # Сохраняем отчет
        with open('advanced_analysis_report.md', 'w', encoding='utf-8') as f:
            f.write(report)

        print("Расширенный отчет сохранен в 'advanced_analysis_report.md'")
        print("Созданы графики:")
        print("- message_patterns.png")
        print("- linguistic_features.png")
        print("- key_phrases_2grams.png")
        print("- key_phrases_3grams.png")
        print("- semantic_similarity.png")

        return report

def main():
    analyzer = AdvancedAnalyzer('parsed_data_20250722_114557.json')
    report = analyzer.create_comprehensive_report()
    print("\nРасширенный анализ завершен!")

if __name__ == "__main__":
    main()
