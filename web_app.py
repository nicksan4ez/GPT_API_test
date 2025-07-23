"""
Веб-интерфейс для анализа телеграм дампов
Поддерживает загрузку файлов, анализ и просмотр результатов с интерактивными графиками
Использует продвинутый анализатор с современными методами NLP
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import plotly.graph_objs as go
import plotly.utils
from working_telegram_analyzer import SimplifiedTelegramAnalyzer
import pandas as pd

app = Flask(__name__)
app.secret_key = 'telegram_analyzer_secret_key_2025'

# Конфигурация
UPLOAD_FOLDER = 'uploads'
REPORTS_FOLDER = 'reports'
TEMP_FOLDER = 'temp'
ALLOWED_EXTENSIONS = {'json', 'txt'}

# Создаем необходимые папки
for folder in [UPLOAD_FOLDER, REPORTS_FOLDER, TEMP_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/test')
def test_page():
    """Тестовая страница для отладки"""
    return render_template('test_index.html')

@app.route('/')
def index():
    """Главная страница с формой загрузки"""
    # Получаем список последних отчетов
    recent_reports = []
    try:
        if os.path.exists(REPORTS_FOLDER):
            reports = [f for f in os.listdir(REPORTS_FOLDER) if f.endswith('.json')]
            reports.sort(key=lambda x: os.path.getctime(os.path.join(REPORTS_FOLDER, x)), reverse=True)
            for report_file in reports[:10]:  # Последние 10 отчетов
                try:
                    with open(os.path.join(REPORTS_FOLDER, report_file), 'r', encoding='utf-8') as f:
                        report_data = json.load(f)
                        recent_reports.append({
                            'id': report_file.replace('.json', ''),
                            'filename': report_data.get('original_filename', 'Неизвестно'),
                            'timestamp': report_data.get('analysis_timestamp', ''),
                            'messages_count': report_data.get('total_messages', 0),
                            'channel_name': report_data.get('channel_info', {}).get('title', 'Неизвестный канал')
                        })
                except Exception as e:
                    print(f"Ошибка при загрузке отчета {report_file}: {e}")
                    continue
    except Exception as e:
        print(f"Ошибка при сканировании папки отчетов: {e}")

    try:
        return render_template('simple_index.html', recent_reports=recent_reports)
    except Exception as e:
        print(f"Ошибка при рендеринге шаблона: {e}")
        return f"""
        <html>
        <head><title>Ошибка</title></head>
        <body>
            <h1>Ошибка рендеринга шаблона</h1>
            <p>Ошибка: {e}</p>
            <p><a href="/test">Перейти к тестовой странице</a></p>
        </body>
        </html>
        """

@app.route('/upload', methods=['POST'])
def upload_file():
    """Обработка загрузки файла"""
    if 'file' not in request.files:
        flash('Файл не выбран', 'error')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Генерируем уникальный ID для анализа
        analysis_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Безопасное имя файла
        filename = secure_filename(file.filename)
        original_filename = filename
        filename = f"{timestamp}_{analysis_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(filepath)

            # Запускаем анализ в фоновом режиме
            return redirect(url_for('analyze_file', analysis_id=analysis_id, filename=filename, original_filename=original_filename))

        except Exception as e:
            flash(f'Ошибка при загрузке файла: {str(e)}', 'error')
            return redirect(request.url)
    else:
        flash('Недопустимый тип файла. Разрешены только .json и .txt файлы', 'error')
        return redirect(request.url)

@app.route('/analyze/<analysis_id>/<filename>')
def analyze_file(analysis_id, filename):
    """Страница анализа файла"""
    original_filename = request.args.get('original_filename', filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        flash('Файл не найден', 'error')
        return redirect(url_for('index'))

    return render_template('simple_analyze.html',
                         analysis_id=analysis_id,
                         filename=filename,
                         original_filename=original_filename)

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API для запуска анализа"""
    data = request.get_json()
    analysis_id = data.get('analysis_id')
    filename = data.get('filename')
    original_filename = data.get('original_filename', filename)

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'Файл не найден'}), 404

    try:
        # Инициализируем анализатор
        analyzer = SimplifiedTelegramAnalyzer()

        # Загружаем данные в зависимости от типа файла
        file_extension = filename.lower().split('.')[-1]

        if file_extension == 'json':
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
            except json.JSONDecodeError:
                return jsonify({
                    'status': 'error',
                    'error': 'Файл не является валидным JSON'
                }), 400
        elif file_extension == 'txt':
            # Для текстовых файлов создаем простую структуру
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text_content = f.read()

                # Разбиваем текст на строки и создаем структуру сообщений
                lines = text_content.split('\n')
                messages = []
                for i, line in enumerate(lines):
                    if line.strip():  # Пропускаем пустые строки
                        messages.append({
                            'id': i,
                            'text': line.strip(),
                            'date': datetime.now().isoformat(),
                            'from': 'unknown'
                        })

                raw_data = {
                    'messages': messages,
                    'name': original_filename,
                    'type': 'text_import'
                }
            except UnicodeDecodeError:
                return jsonify({
                    'status': 'error',
                    'error': 'Не удается прочитать файл. Проверьте кодиро��ку (должна быть UTF-8)'
                }), 400
        else:
            return jsonify({
                'status': 'error',
                'error': 'Неподдерживаемый формат файла'
            }), 400

        # Адаптируем данные под наш формат
        adapted_data = analyzer.adapt_export_data(raw_data)

        if adapted_data['total_count'] == 0:
            return jsonify({
                'status': 'error',
                'error': 'В файле н�� найдено сообщений для анализа'
            }), 400

        # Проводим комплексный анализ
        analysis_results = analyzer.analyze_comprehensive(raw_data)

        # Создаем отчет для Telegram
        telegram_report = analyzer.generate_telegram_report(analysis_results)

        # Добавляем метаданные
        analysis_results.update({
            'analysis_id': analysis_id,
            'original_filename': original_filename,
            'analysis_timestamp': datetime.now().isoformat(),
            'file_size_bytes': os.path.getsize(filepath),
            'telegram_report': telegram_report
        })

        # Сохраняем результаты
        report_path = os.path.join(REPORTS_FOLDER, f"{analysis_id}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)

        return jsonify({
            'status': 'completed',
            'analysis_id': analysis_id,
            'results': analysis_results
        })

    except Exception as e:
        print(f"Ошибка анализа: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': f'Ошибка при анализе: {str(e)}'
        }), 500

@app.route('/report/<analysis_id>')
def view_report(analysis_id):
    """Просмотр отчета с интерактивными графиками"""
    report_path = os.path.join(REPORTS_FOLDER, f"{analysis_id}.json")

    if not os.path.exists(report_path):
        flash('Отчет не найден', 'error')
        return redirect(url_for('index'))

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        # Создаем интерактивные графики
        charts = create_interactive_charts(report_data)

        return render_template('simple_report.html',
                             report=report_data,
                             charts=charts,
                             analysis_id=analysis_id)

    except Exception as e:
        flash(f'Ошибка при загрузке отчета: {str(e)}', 'error')
        return redirect(url_for('index'))

def create_interactive_charts(report_data):
    """Создает интерактивные графики для отчета с новой структурой данных"""
    charts = {}

    try:
        # График частотного анализа слов
        if 'frequency_analysis' in report_data:
            freq_data = report_data['frequency_analysis']

            if 'top_words' in freq_data and freq_data['top_words']:
                top_words = freq_data['top_words'][:20]
                words = [item[0] for item in top_words]
                counts = [item[1] for item in top_words]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=words[::-1],  # Переворачиваем для горизонтального отображения
                    x=counts[::-1],
                    orientation='h',
                    marker_color='rgba(255, 127, 14, 0.7)',
                    hovertemplate='Слово: %{y}<br>Частота: %{x}<extra></extra>'
                ))

                fig.update_layout(
                    title='Топ-20 наиболее частых слов',
                    xaxis_title='Частота использования',
                    yaxis_title='Слова',
                    template='plotly_white',
                    height=600
                )

                charts['frequency_words'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

            # График биграмм
            if 'top_bigrams' in freq_data and freq_data['top_bigrams']:
                top_bigrams = freq_data['top_bigrams'][:15]
                bigrams = [item[0] for item in top_bigrams]
                counts = [item[1] for item in top_bigrams]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=bigrams[::-1],
                    x=counts[::-1],
                    orientation='h',
                    marker_color='rgba(44, 160, 44, 0.7)',
                    hovertemplate='Словосочетание: %{y}<br>Частота: %{x}<extra></extra>'
                ))

                fig.update_layout(
                    title='Топ-15 словосочетаний',
                    xaxis_title='Частота использования',
                    yaxis_title='Словосочетания',
                    template='plotly_white',
                    height=500
                )

                charts['bigrams'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # График анализа тональности
        if 'sentiment_analysis' in report_data and report_data['sentiment_analysis']:
            sentiment_data = report_data['sentiment_analysis']

            # Подсчитываем распределение тональности
            sentiment_counts = {}
            for item in sentiment_data:
                sentiment = item.get('overall', 'neutral')
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

            if sentiment_counts:
                # Переводим названия на русский
                sentiment_labels = {
                    'positive': 'Позитивные',
                    'negative': 'Негативные',
                    'neutral': 'Нейтральные',
                    'skip': 'Пропущенные',
                    'speech': 'Речевые'
                }

                labels = [sentiment_labels.get(k, k.title()) for k in sentiment_counts.keys()]
                values = list(sentiment_counts.values())
                colors = ['rgba(44, 160, 44, 0.7)', 'rgba(214, 39, 40, 0.7)',
                         'rgba(128, 128, 128, 0.7)', 'rgba(255, 193, 7, 0.7)',
                         'rgba(54, 162, 235, 0.7)']

                fig = go.Figure()
                fig.add_trace(go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,
                    marker_colors=colors[:len(labels)],
                    hovertemplate='Тип: %{label}<br>Количество: %{value}<br>Процент: %{percent}<extra></extra>'
                ))

                fig.update_layout(
                    title='Распределение тональности сообщений',
                    template='plotly_white'
                )

                charts['sentiment'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # График тематического моделирования
        if 'topic_modeling' in report_data and report_data['topic_modeling']:
            topic_data = report_data['topic_modeling']

            if 'topics' in topic_data and topic_data['topics']:
                topics = topic_data['topics']

                # Создаем график для каждой темы (только первые 3 темы для читаемости)
                for i, topic in enumerate(topics[:3]):
                    words = topic['words'][:8]  # Топ-8 слов для каждой темы
                    weights = topic['weights'][:8]

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=weights,
                        y=words,
                        orientation='h',
                        marker_color=f'rgba({50 + i * 70}, {100 + i * 50}, {200 - i * 30}, 0.7)',
                        hovertemplate='Слово: %{y}<br>Вес: %{x:.3f}<extra></extra>'
                    ))

                    fig.update_layout(
                        title=f'Тема {i + 1}: {topic.get("description", "Без описания")}',
                        xaxis_title='Вес слова в теме',
                        yaxis_title='Слова',
                        template='plotly_white',
                        height=400
                    )

                    charts[f'topic_{i + 1}'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # График базовой статистики
        if 'basic_stats' in report_data:
            stats = report_data['basic_stats']

            metrics = ['Всего сообщений', 'Текстовых сообщений', 'Средняя длина']
            values = [
                stats.get('total_messages', 0),
                stats.get('total_texts', 0),
                int(stats.get('avg_message_length', 0))
            ]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=metrics,
                y=values,
                marker_color=['rgba(31, 119, 180, 0.7)', 'rgba(255, 127, 14, 0.7)', 'rgba(44, 160, 44, 0.7)'],
                hovertemplate='Метрика: %{x}<br>Значение: %{y}<extra></extra>'
            ))

            fig.update_layout(
                title='Основная статистика канала',
                xaxis_title='Метрики',
                yaxis_title='Значения',
                template='plotly_white'
            )

            charts['basic_stats'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # График связанности слов (если есть данные о графе)
        if 'word_connections' in report_data and report_data['word_connections']:
            conn_data = report_data['word_connections']

            if 'centrality' in conn_data and conn_data['centrality']:
                centrality = conn_data['centrality']

                if 'degree' in centrality:
                    # Топ-15 слов по центральности
                    top_central = sorted(centrality['degree'].items(),
                                       key=lambda x: x[1], reverse=True)[:15]

                    words = [item[0] for item in top_central]
                    scores = [item[1] for item in top_central]

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        y=words[::-1],
                        x=scores[::-1],
                        orientation='h',
                        marker_color='rgba(156, 39, 176, 0.7)',
                        hovertemplate='Слово: %{y}<br>Центральность: %{x:.3f}<extra></extra>'
                    ))

                    fig.update_layout(
                        title='Ключевые слова по связанности',
                        xaxis_title='Коэффициент центральности',
                        yaxis_title='Слова',
                        template='plotly_white',
                        height=500
                    )

                    charts['word_centrality'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    except Exception as e:
        print(f"Ошибка при создании графиков: {e}")
        import traceback
        traceback.print_exc()

    return charts

@app.route('/api/reports')
def api_reports():
    """API для получения списка отчетов"""
    reports = []
    if os.path.exists(REPORTS_FOLDER):
        for filename in os.listdir(REPORTS_FOLDER):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(REPORTS_FOLDER, filename), 'r', encoding='utf-8') as f:
                        report_data = json.load(f)
                        reports.append({
                            'id': filename.replace('.json', ''),
                            'filename': report_data.get('original_filename', 'Неизвестно'),
                            'timestamp': report_data.get('analysis_timestamp', ''),
                            'messages_count': report_data.get('total_messages', 0)
                        })
                except:
                    continue

    return jsonify(reports)

@app.route('/download/<analysis_id>')
def download_report(analysis_id):
    """Скачивание отчета в JSON формате"""
    report_path = os.path.join(REPORTS_FOLDER, f"{analysis_id}.json")

    if not os.path.exists(report_path):
        flash('Отчет не найден', 'error')
        return redirect(url_for('index'))

    return send_file(report_path, as_attachment=True, download_name=f"telegram_analysis_{analysis_id}.json")

@app.route('/telegram_report/<analysis_id>')
def get_telegram_report(analysis_id):
    """Получение отчета в формате для Telegram"""
    report_path = os.path.join(REPORTS_FOLDER, f"{analysis_id}.json")

    if not os.path.exists(report_path):
        return jsonify({'error': 'Отчет не найден'}), 404

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        telegram_report = report_data.get('telegram_report', 'Отчет не найден')

        return jsonify({
            'telegram_report': telegram_report,
            'analysis_id': analysis_id,
            'formatted_for_telegram': True
        })

    except Exception as e:
        return jsonify({'error': f'Ошибка при получении отчета: {str(e)}'}), 500

@app.route('/download_telegram/<analysis_id>')
def download_telegram_report(analysis_id):
    """Скачивание отчета в текстовом формате для Telegram"""
    report_path = os.path.join(REPORTS_FOLDER, f"{analysis_id}.json")

    if not os.path.exists(report_path):
        flash('Отчет не найден', 'error')
        return redirect(url_for('index'))

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        telegram_report = report_data.get('telegram_report', 'Отчет не найден')

        # Создаем временный файл с отчетом
        txt_filename = f"telegram_report_{analysis_id}.txt"
        txt_path = os.path.join(TEMP_FOLDER, txt_filename)

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(telegram_report)

        return send_file(txt_path, as_attachment=True, download_name=txt_filename)

    except Exception as e:
        flash(f'Ошибка при создании отчета: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
