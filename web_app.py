"""
Веб-интерфейс для анализа телеграм дампов
Поддерживает загрузку файлов, анализ и просмотр результатов с интерактивными графиками
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import plotly.graph_objs as go
import plotly.utils
from telegram_analyzer_web import TelegramAnalyzer
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
        analyzer = TelegramAnalyzer()

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

        # Проводим анализ
        analysis_results = analyzer.analyze_messages(adapted_data)

        # Добавляем метаданные
        analysis_results.update({
            'analysis_id': analysis_id,
            'original_filename': original_filename,
            'analysis_timestamp': datetime.now().isoformat(),
            'file_size_bytes': os.path.getsize(filepath)
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
    """Создает интерактивные графики для отчета"""
    charts = {}

    try:
        # График активности по времени
        if 'time_analysis' in report_data:
            time_data = report_data['time_analysis']

            # График активности по часам
            if 'hourly_distribution' in time_data:
                hours = list(range(24))
                counts = [time_data['hourly_distribution'].get(str(h), 0) for h in hours]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=hours,
                    y=counts,
                    name='Сообщения по часам',
                    marker_color='rgba(55, 128, 191, 0.7)',
                    hovertemplate='Час: %{x}<br>Сообщени��: %{y}<extra></extra>'
                ))

                fig.update_layout(
                    title='Активность по часам дня',
                    xaxis_title='Час дня',
                    yaxis_title='Количество сообщений',
                    template='plotly_white'
                )

                charts['hourly_activity'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # График топ слов
        if 'word_analysis' in report_data and 'top_words' in report_data['word_analysis']:
            top_words = report_data['word_analysis']['top_words'][:20]
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

            charts['top_words'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # График длины сообщений
        if 'message_stats' in report_data:
            stats = report_data['message_stats']

            # С��здаем гистограмму длин сообщений (если есть детальные данные)
            fig = go.Figure()

            # Добавляем показатели как bar chart
            metrics = ['Среднее', 'Медиана', 'Максимум']
            values = [
                stats.get('average_length', 0),
                stats.get('median_length', 0),
                stats.get('max_length', 0)
            ]

            fig.add_trace(go.Bar(
                x=metrics,
                y=values,
                marker_color=['rgba(31, 119, 180, 0.7)', 'rgba(255, 127, 14, 0.7)', 'rgba(44, 160, 44, 0.7)'],
                hovertemplate='Метрика: %{x}<br>Значение: %{y}<extra></extra>'
            ))

            fig.update_layout(
                title='Статистика длины сообщений',
                xaxis_title='Метрики',
                yaxis_title='Количество символов',
                template='plotly_white'
            )

            charts['message_length'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # График тональности (если есть)
        if 'sentiment_analysis' in report_data:
            sentiment = report_data['sentiment_analysis']

            labels = ['Позитивные', 'Нейтральные', 'Негативные']
            values = [
                sentiment.get('positive_count', 0),
                sentiment.get('neutral_count', 0),
                sentiment.get('negative_count', 0)
            ]

            fig = go.Figure()
            fig.add_trace(go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker_colors=['rgba(44, 160, 44, 0.7)', 'rgba(128, 128, 128, 0.7)', 'rgba(214, 39, 40, 0.7)'],
                hovertemplate='Тип: %{label}<br>Количество: %{value}<br>Процент: %{percent}<extra></extra>'
            ))

            fig.update_layout(
                title='Распределение тональности сообщений',
                template='plotly_white'
            )

            charts['sentiment'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    except Exception as e:
        print(f"Ошибка при создании графиков: {e}")

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
