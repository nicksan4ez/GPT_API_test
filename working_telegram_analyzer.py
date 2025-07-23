"""
Упрощенный но мощный анализатор Telegram с современными методами NLP
Включает тематическое моделирование, анализ тональности, визуализацию и отчеты для Telegram
Работает без проблемных зависимостей
"""

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
from wordcloud import WordCloud
import base64
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# NLP библиотеки (с обработкой ошибок)
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    print("NLTK не установлен, используем базовые методы")
    NLTK_AVAILABLE = False

try:
    from stop_words import get_stop_words
    STOP_WORDS_AVAILABLE = True
except ImportError:
    print("stop-words не установлен")
    STOP_WORDS_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    print("Scikit-learn не доступен")
    SKLEARN_AVAILABLE = False

class SimplifiedTelegramAnalyzer:
    def __init__(self):
        self.stop_words = self.get_comprehensive_stop_words()
        self.setup_visualization_style()
        
    def get_comprehensive_stop_words(self):
        """Получает комплексный набор русских стоп-слов из различных источников"""
        stop_words_set = set()
        
        # Стоп-слова из NLTK
        if NLTK_AVAILABLE:
            try:
                nltk_stopwords = set(stopwords.words('russian'))
                stop_words_set.update(nltk_stopwords)
            except:
                pass
        
        # Стоп-слова из библиотеки stop-words
        if STOP_WORDS_AVAILABLE:
            try:
                sw_stopwords = set(get_stop_words('russian'))
                stop_words_set.update(sw_stopwords)
            except:
                pass
        
        # Расширенный набор собственных стоп-слов
        custom_stopwords = {
            # Местоимения
            'я', 'мы', 'ты', 'вы', 'он', 'она', 'оно', 'они',
            'мой', 'моя', 'мое', 'мои', 'твой', 'твоя', 'твое', 'твои',
            'наш', 'наша', 'наше', 'наши', 'ваш', 'ваша', 'ваше', 'ваши',
            'его', 'ее', 'их', 'себя', 'себе', 'собой', 'собою', 'меня', 'тебя',
            
            # Служебные слова и предлоги
            'и', 'а', 'но', 'или', 'да', 'нет', 'не', 'ни', 'же', 'ли', 'бы',
            'что', 'как', 'где', 'когда', 'почему', 'зачем', 'так', 'тут', 'там',
            'это', 'эта', 'этот', 'эти', 'то', 'та', 'тот', 'те', 'в', 'на', 'с',
            'по', 'для', 'от', 'до', 'из', 'к', 'о', 'об', 'при', 'за', 'под',
            'над', 'через', 'между', 'среди', 'без', 'около', 'возле',
            
            # Указательные и вопросительные
            'такой', 'такая', 'такое', 'такие', 'который', 'которая', 'которое', 'которые',
            'кто', 'куда', 'откуда', 'сколько', 'какой', 'какая', 'какое', 'какие',
            'чей', 'чья', 'чье', 'чьи',
            
            # Союзы и частицы
            'либо', 'тоже', 'также', 'если', 'чтобы', 'потому', 'поэтому', 'ведь',
            'уже', 'еще', 'ещё', 'вот', 'вон', 'здесь', 'сюда', 'туда', 'отсюда',
            'оттуда', 'везде', 'всюду', 'нигде', 'никуда', 'очень', 'весьма',
            'довольно', 'совсем', 'почти', 'слишком', 'едва', 'вдруг', 'сейчас',
            'теперь', 'потом', 'тогда', 'всегда', 'никогда', 'иногда', 'часто',
            'редко', 'рано', 'поздно', 'давно', 'недавно',
            
            # Количественные
            'один', 'одна', 'одно', 'одни', 'два', 'две', 'три', 'четыре', 'пять',
            'много', 'мало', 'несколько', 'все', 'всё', 'всех', 'всем', 'всему',
            'каждый', 'каждая', 'каждое', 'любой', 'любая', 'любое', 'другой',
            
            # Глаголы-связки
            'быть', 'есть', 'был', 'была', 'было', 'были', 'буду', 'будешь', 'будет',
            'будем', 'будете', 'будут', 'бывать', 'стать', 'стал', 'стала', 'стало',
            'стали', 'мочь', 'могу', 'можешь', 'может', 'можем', 'можете', 'могут',
            'мог', 'могла', 'хотеть', 'хочу', 'хочешь', 'хочет', 'хотим', 'хотите',
            'хотят', 'хотел',
            
            # Общие слова
            'просто', 'только', 'пока', 'именно', 'конечно', 'наверное', 'возможно',
            'вообще', 'кстати', 'прочим', 'кроме', 'того', 'помимо', 'включая',
            'исключая', 'вам', 'нам', 'тем', 'более', 'менее', 'самый', 'самая',
            'самое', 'самые', 'лучше', 'хуже', 'больше', 'меньше', 'выше', 'ниже',
            
            # Технические слова Telegram и интернет
            'https', 'http', 'www', 'com', 'ru', 'org', 'net', 't', 'me',
            'channel', 'chat', 'bot', 'forward', 'reply', 'edit', 'forwarded',
            'telegram', 'тг', 'канал', 'чат', 'бот', 'переслано', 'ответ',
            
            # Частые междометия и сленг
            'ага', 'ок', 'окей', 'да', 'нет', 'ну', 'вот', 'эм', 'хм', 'ммм',
            'лол', 'кек', 'хаха', 'ахах', 'хех', 'блин', 'типа', 'короче',
            'капец', 'пипец', 'офигеть', 'зачёт', 'круто', 'прикол', 'жесть',
            'норм', 'чё', 'шо', 'чего', 'чота', 'хз', 'пхп', 'имхо',
        }
        
        stop_words_set.update(custom_stopwords)
        
        # Добавляем числа как стоп-слова
        numbers = {str(i) for i in range(100)}
        stop_words_set.update(numbers)
        
        return stop_words_set

    def setup_visualization_style(self):
        """Настройка стиля для визуализации"""
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        
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
        """Продвинутая очистка текста"""
        if not text:
            return ""

        # Убираем URL
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'www\.[^\s]+', '', text)
        text = re.sub(r't\.me/[^\s]+', '', text)

        # Убираем mentions и hashtags
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)

        # Убираем эмодзи и специальные символы
        text = re.sub(r'[^\w\s\-]', ' ', text)
        
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Приводим к нижнему регистру
        text = text.lower().strip()

        return text

    def simple_lemmatize(self, word):
        """Простая лемматизация на основе правил для русского языка"""
        # Простые правила для удаления окончаний
        suffixes = ['ов', 'ев', 'ами', 'ях', 'ах', 'ем', 'ом', 'ей', 'ой', 'ий', 'ый', 'ая', 'ое', 'ые', 'ие']
        
        # Удаляем распространенные окончания
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        
        return word

    def tokenize_and_lemmatize(self, text):
        """Токенизация и простая лемматизация текста"""
        if not text:
            return []
            
        # Базовая токенизация
        words = re.findall(r'\b[а-яё]{2,}\b', text.lower())
        
        # Простая лемматизация
        words = [self.simple_lemmatize(word) for word in words]
        
        # Фильтрация стоп-слов
        words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        return words

    def analyze_sentiment(self, texts):
        """Простой анализ тональности на основе словарей"""
        results = []
        
        # Словари для анализа тональности
        positive_words = {
            'хорошо', 'отлично', 'супер', 'круто', 'класс', 'зачёт', 'молодец',
            'прекрасно', 'замечательно', 'великолепно', 'чудесно', 'превосходно',
            'радость', 'счастье', 'любовь', 'восторг', 'восхищение', 'удовольствие',
            'спасибо', 'благодарю', 'рад', 'рада', 'довольный', 'довольна',
            'нравится', 'люблю', 'обожаю', 'кайф', 'красота', 'красиво'
        }
        
        negative_words = {
            'плохо', 'ужасно', 'гадость', 'фигня', 'дрянь', 'отстой', 'кошмар',
            'ненавижу', 'злость', 'гнев', 'раздражение', 'досада', 'печаль',
            'грусть', 'тоска', 'депрессия', 'расстройство', 'разочарование',
            'бесит', 'раздражает', 'надоело', 'устал', 'устала', 'скучно',
            'противно', 'мерзко', 'отвратительно', 'жуть', 'капец', 'пипец'
        }
        
        for text in texts:
            sentiment_result = {
                'text': text[:100] + '...' if len(text) > 100 else text,
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 0.0,
                'overall': 'neutral'
            }
            
            # Анализируем текст
            text_words = set(text.lower().split())
            pos_count = len(text_words.intersection(positive_words))
            neg_count = len(text_words.intersection(negative_words))
            
            total_sentiment_words = pos_count + neg_count
            
            if total_sentiment_words > 0:
                sentiment_result['positive'] = pos_count / max(total_sentiment_words, 1)
                sentiment_result['negative'] = neg_count / max(total_sentiment_words, 1)
                sentiment_result['neutral'] = 0.0
                
                if pos_count > neg_count:
                    sentiment_result['overall'] = 'positive'
                elif neg_count > pos_count:
                    sentiment_result['overall'] = 'negative'
                else:
                    sentiment_result['overall'] = 'neutral'
            else:
                sentiment_result['neutral'] = 1.0
                sentiment_result['overall'] = 'neutral'
            
            results.append(sentiment_result)
        
        return results

    def perform_topic_modeling(self, texts, num_topics=5):
        """Тематическое моделирование с LDA"""
        if not SKLEARN_AVAILABLE:
            return None, "Scikit-learn не установлен"
            
        try:
            # Подготовка текстов
            cleaned_texts = []
            for text in texts:
                cleaned = self.clean_text(text)
                tokens = self.tokenize_and_lemmatize(cleaned)
                if len(tokens) > 3:  # Минимум 3 значимых слова
                    cleaned_texts.append(' '.join(tokens))
            
            if len(cleaned_texts) < 5:
                return None, "Недостаточно текстов для тематического моделирования"
            
            # Векторизация
            vectorizer = CountVectorizer(
                max_features=1000,
                min_df=2,
                max_df=0.8,
                ngram_range=(1, 2)
            )
            
            doc_term_matrix = vectorizer.fit_transform(cleaned_texts)
            
            # LDA модель
            lda = LatentDirichletAllocation(
                n_components=num_topics,
                random_state=42,
                max_iter=100,
                learning_method='online'
            )
            
            lda.fit(doc_term_matrix)
            
            # Извлечение тем
            feature_names = vectorizer.get_feature_names_out()
            topics = []
            
            for topic_idx, topic in enumerate(lda.components_):
                top_words_idx = topic.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_words_idx]
                topic_weights = [topic[i] for i in top_words_idx]
                
                topics.append({
                    'id': topic_idx,
                    'words': top_words,
                    'weights': topic_weights,
                    'description': ', '.join(top_words[:5])
                })
            
            # Распределение документов по темам
            doc_topic_probs = lda.transform(doc_term_matrix)
            
            return {
                'topics': topics,
                'doc_topic_probs': doc_topic_probs.tolist(),
                'perplexity': lda.perplexity(doc_term_matrix)
            }, None
            
        except Exception as e:
            return None, f"Ошибка тематического моделирования: {str(e)}"

    def frequency_analysis(self, texts):
        """Частотный анализ слов"""
        all_words = []
        
        for text in texts:
            cleaned = self.clean_text(text)
            tokens = self.tokenize_and_lemmatize(cleaned)
            all_words.extend(tokens)
        
        # Подсчет частот
        word_freq = Counter(all_words)
        
        # Топ слов
        top_words = word_freq.most_common(50)
        
        # N-граммы (биграммы)
        bigrams = []
        for text in texts:
            tokens = self.tokenize_and_lemmatize(self.clean_text(text))
            if len(tokens) > 1:
                for i in range(len(tokens) - 1):
                    bigram = f"{tokens[i]} {tokens[i+1]}"
                    bigrams.append(bigram)
        
        bigram_freq = Counter(bigrams) if bigrams else Counter()
        top_bigrams = bigram_freq.most_common(20)
        
        return {
            'total_words': len(all_words),
            'unique_words': len(word_freq),
            'top_words': top_words,
            'top_bigrams': top_bigrams,
            'word_frequencies': dict(word_freq)
        }

    def analyze_word_connections(self, texts, min_cooccurrence=2):
        """Анализ связей между словами"""
        if not texts:
            return None
            
        # Создаем граф слов
        G = nx.Graph()
        word_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        # Анализируем сосуществование слов в предложениях
        for text in texts:
            cleaned = self.clean_text(text)
            tokens = self.tokenize_and_lemmatize(cleaned)
            
            # Добавляем связи между словами в пределах окна
            window_size = 5
            for i, word1 in enumerate(tokens):
                for j in range(i + 1, min(i + window_size, len(tokens))):
                    word2 = tokens[j]
                    if word1 != word2:
                        word_cooccurrence[word1][word2] += 1
                        word_cooccurrence[word2][word1] += 1
        
        # Создаем граф
        edges_list = []
        for word1, connections in word_cooccurrence.items():
            for word2, weight in connections.items():
                if weight >= min_cooccurrence:
                    G.add_edge(word1, word2, weight=weight)
                    # збегаем дублирования рёбер в списке
                    if word1 < word2:  # лексикографический порядок
                        edges_list.append([word1, word2, weight])
        
        # Анализ центральности
        centrality = {}
        if len(G.nodes()) > 0:
            try:
                centrality = {
                    'degree': nx.degree_centrality(G),
                    'betweenness': nx.betweenness_centrality(G),
                    'closeness': nx.closeness_centrality(G),
                }
                
                # eigenvector_centrality может не сработать для некоторых графов
                try:
                    centrality['eigenvector'] = nx.eigenvector_centrality(G, max_iter=1000)
                except:
                    centrality['eigenvector'] = {}
                    
            except Exception as e:
                print(f"Ошибка анализа центральности: {e}")
                centrality = {'degree': {}, 'betweenness': {}, 'closeness': {}, 'eigenvector': {}}
        
        return {
            'graph': {
                'nodes': list(G.nodes()),
                'edges': edges_list
            },
            'centrality': centrality,
            'nodes_count': len(G.nodes()),
            'edges_count': len(G.edges()),
            'density': nx.density(G) if len(G.nodes()) > 1 else 0
        }

    def analyze_comprehensive(self, raw_data):
        """Комплексный анализ данных"""
        try:
            # Адаптация данных
            adapted_data = self.adapt_export_data(raw_data)
            messages = adapted_data['messages']
            
            if not messages:
                raise ValueError("Нет сообщений для анализа")
            
            # Извлекаем тексты
            texts = [msg['text'] for msg in messages if msg.get('text')]
            
            if not texts:
                raise ValueError("Нет текстов для анализа")
            
            print(f"Анализируем {len(texts)} сообщений...")
            
            # Выполняем все виды анализа
            results = {
                'basic_stats': {
                    'total_messages': len(messages),
                    'total_texts': len(texts),
                    'avg_message_length': np.mean([len(text) for text in texts]),
                    'channel_info': adapted_data['channel_info']
                }
            }
            
            # Частотный анализ
            print("Выполняем частотный анализ...")
            results['frequency_analysis'] = self.frequency_analysis(texts)
            
            # Анализ тональности
            print("Выполняем анализ тональности...")
            results['sentiment_analysis'] = self.analyze_sentiment(texts)
            
            # Тематическое моделирование
            print("Выполняем тематическое моделирование...")
            topic_result, topic_error = self.perform_topic_modeling(texts)
            if topic_result:
                results['topic_modeling'] = topic_result
            else:
                results['topic_modeling_error'] = topic_error
            
            # Анализ связей слов
            print("Анализируем связи между словами...")
            results['word_connections'] = self.analyze_word_connections(texts)
            
            return results
            
        except Exception as e:
            raise Exception(f"Ошибка комплексного анализа: {str(e)}")

    def generate_telegram_report(self, analysis_results):
        """Генерация отчета в формате, удобном для Telegram"""
        try:
            report_lines = []
            
            # Заголовок
            report_lines.append("📊 АНАЛИЗ TELEGRAM КАНАЛА")
            report_lines.append("=" * 30)
            report_lines.append("")
            
            # Базовая статистика
            basic_stats = analysis_results.get('basic_stats', {})
            channel_info = basic_stats.get('channel_info', {})
            
            report_lines.append(f"📢 Канал: {channel_info.get('title', 'Неизвестно')}")
            report_lines.append(f"📝 Всего сообщений: {basic_stats.get('total_messages', 0)}")
            report_lines.append(f"📄 Текстовых сообщений: {basic_stats.get('total_texts', 0)}")
            report_lines.append(f"📏 Средняя длина сообщения: {basic_stats.get('avg_message_length', 0):.1f} символов")
            report_lines.append("")
            
            # Частотный анализ
            freq_analysis = analysis_results.get('frequency_analysis', {})
            if freq_analysis:
                report_lines.append("🔤 ЧАСТОТНЫЙ АНАЛИЗ")
                report_lines.append("-" * 20)
                report_lines.append(f"Всего слов: {freq_analysis.get('total_words', 0)}")
                report_lines.append(f"Уникальных слов: {freq_analysis.get('unique_words', 0)}")
                report_lines.append("")
                
                report_lines.append("🏆 Топ-10 слов:")
                top_words = freq_analysis.get('top_words', [])[:10]
                for i, (word, count) in enumerate(top_words, 1):
                    report_lines.append(f"{i}. {word}: {count}")
                report_lines.append("")
                
                if freq_analysis.get('top_bigrams'):
                    report_lines.append("🔗 Топ-5 словосочетаний:")
                    top_bigrams = freq_analysis.get('top_bigrams', [])[:5]
                    for i, (bigram, count) in enumerate(top_bigrams, 1):
                        report_lines.append(f"{i}. {bigram}: {count}")
                    report_lines.append("")
            
            # Анализ тональности
            sentiment_analysis = analysis_results.get('sentiment_analysis', [])
            if sentiment_analysis:
                sentiment_counts = Counter([item['overall'] for item in sentiment_analysis])
                total_analyzed = len(sentiment_analysis)
                
                report_lines.append("😊 АНАЛИЗ ТОНАЛЬНОСТИ")
                report_lines.append("-" * 20)
                
                sentiment_emojis = {
                    'positive': '😊',
                    'negative': '😞', 
                    'neutral': '😐',
                }
                
                for sentiment, count in sentiment_counts.most_common():
                    percentage = (count / total_analyzed) * 100
                    emoji = sentiment_emojis.get(sentiment, '❓')
                    report_lines.append(f"{emoji} {sentiment.title()}: {count} ({percentage:.1f}%)")
                report_lines.append("")
            
            # Тематическое моделирование
            topic_modeling = analysis_results.get('topic_modeling')
            if topic_modeling and topic_modeling.get('topics'):
                report_lines.append("🎯 ОСНОВНЫЕ ТЕМЫ")
                report_lines.append("-" * 20)
                
                topics = topic_modeling['topics']
                for i, topic in enumerate(topics[:5], 1):
                    top_words = ', '.join(topic['words'][:5])
                    report_lines.append(f"{i}. {top_words}")
                report_lines.append("")
            
            # Связи между словами
            word_connections = analysis_results.get('word_connections', {})
            if word_connections and word_connections.get('centrality'):
                centrality = word_connections['centrality']
                
                report_lines.append("🕸️ КЛЮЧЕВЫЕ СЛОВА (по связанности)")
                report_lines.append("-" * 20)
                
                if 'degree' in centrality:
                    top_central_words = sorted(
                        centrality['degree'].items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:10]
                    
                    for i, (word, centrality_score) in enumerate(top_central_words, 1):
                        report_lines.append(f"{i}. {word} (связей: {centrality_score:.3f})")
                report_lines.append("")
            
            # Заключение
            report_lines.append("📈 КРАТКИЕ ВЫВОДЫ")
            report_lines.append("-" * 20)
            
            # Автоматические выводы на основе анализа
            conclusions = []
            
            if sentiment_analysis:
                sentiment_counts = Counter([item['overall'] for item in sentiment_analysis])
                pos_ratio = sentiment_counts.get('positive', 0) / len(sentiment_analysis)
                neg_ratio = sentiment_counts.get('negative', 0) / len(sentiment_analysis)
                
                if pos_ratio > 0.4:
                    conclusions.append("• Преобладает позитивная тональность общения")
                elif neg_ratio > 0.4:
                    conclusions.append("• Преобладает негативная тональность общения")
                else:
                    conclusions.append("• Нейтральная тональность общения")
            
            if freq_analysis:
                unique_ratio = freq_analysis.get('unique_words', 0) / max(freq_analysis.get('total_words', 1), 1)
                if unique_ratio > 0.3:
                    conclusions.append("• Богатый словарный запас участников")
                else:
                    conclusions.append("• Ограниченный словарный запас или повторяющиеся темы")
            
            if word_connections:
                density = word_connections.get('density', 0)
                if density > 0.1:
                    conclusions.append("• Высокая связанность тем в обсуждениях")
                else:
                    conclusions.append("• Разрозненные темы обсуждений")
            
            for conclusion in conclusions:
                report_lines.append(conclusion)
            
            report_lines.append("")
            report_lines.append(f"🕐 Отчет сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            
            return '\n'.join(report_lines)
            
        except Exception as e:
            return f"Ошибка генерации отчета: {str(e)}"

if __name__ == "__main__":
    # Пример использования
    analyzer = SimplifiedTelegramAnalyzer()
    
    # Тестовые данные
    test_data = {
        "messages": [
            {"text": "Привет всем! Как дела?", "date": "2025-01-01", "from": "user1"},
            {"text": "Отлично! Сегодня прекрасная погода", "date": "2025-01-01", "from": "user2"},
            {"text": "Согласен, очень хорошо", "date": "2025-01-01", "from": "user3"},
            {"text": "А у меня плохое настроение", "date": "2025-01-01", "from": "user4"},
            {"text": "Не грусти, все будет хорошо!", "date": "2025-01-01", "from": "user1"},
            {"text": "Кто-нибудь знает про новые возможности в Python?", "date": "2025-01-01", "from": "user5"},
            {"text": "Python развивается очень быстро, много новых библиотек", "date": "2025-01-01", "from": "user6"},
            {"text": "Особенно интересны машинное обучение и анализ данных", "date": "2025-01-01", "from": "user7"},
            {"text": "Да, scikit-learn и pandas просто замечательные инструменты", "date": "2025-01-01", "from": "user8"}
        ]
    }
    
    try:
        print("Запускаем комплексный анализ...")
        results = analyzer.analyze_comprehensive(test_data)
        
        print("\nГенерируем отчет для Telegram...")
        telegram_report = analyzer.generate_telegram_report(results)
        
        print("Анализ завершен!")
        print("\nОтчет для Telegram:")
        print("=" * 50)
        print(telegram_report)
        
    except Exception as e:
        print(f"Ошибка: {e}")
