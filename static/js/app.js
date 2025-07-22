/**
 * Основные JavaScript функции для анализатора Telegram дампов
 */

class TelegramAnalyzerApp {
    constructor() {
        this.initializeApp();
    }

    initializeApp() {
        this.setupEventListeners();
        this.initializeAnimations();
        this.setupProgressTracking();
    }

    setupEventListeners() {
        // Обработка загрузки файлов
        const fileInput = document.getElementById('file');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        // Drag & Drop улучшения
        this.setupAdvancedDragDrop();

        // Кнопки действий
        this.setupActionButtons();
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        const fileInfo = document.querySelector('.file-info');
        const uploadBtn = document.getElementById('uploadBtn');

        if (this.validateFile(file)) {
            this.displayFileInfo(file, fileInfo);
            if (uploadBtn) uploadBtn.disabled = false;
        } else {
            this.showError('Неподдерживаемый формат файла');
            if (uploadBtn) uploadBtn.disabled = true;
        }
    }

    validateFile(file) {
        const allowedTypes = ['application/json', 'text/plain'];
        const maxSize = 100 * 1024 * 1024; // 100MB

        if (!allowedTypes.includes(file.type) && !file.name.match(/\.(json|txt)$/i)) {
            return false;
        }

        if (file.size > maxSize) {
            this.showError('Файл слишком большой. Максимальный размер: 100MB');
            return false;
        }

        return true;
    }

    displayFileInfo(file, container) {
        if (!container) return;

        const fileSize = this.formatFileSize(file.size);
        const fileType = this.getFileTypeIcon(file.name);

        container.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="${fileType.icon} fa-2x text-${fileType.color}"></i>
                </div>
                <div class="flex-grow-1">
                    <h6 class="mb-1">${file.name}</h6>
                    <small class="text-muted">
                        Размер: ${fileSize} | Тип: ${fileType.label}
                    </small>
                </div>
                <div>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="telegramApp.clearFile()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        container.style.display = 'block';
        container.classList.add('animate-in');
    }

    getFileTypeIcon(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        switch (extension) {
            case 'json':
                return { icon: 'fas fa-file-code', color: 'primary', label: 'JSON' };
            case 'txt':
                return { icon: 'fas fa-file-alt', color: 'success', label: 'Text' };
            default:
                return { icon: 'fas fa-file', color: 'secondary', label: 'Файл' };
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    clearFile() {
        const fileInput = document.getElementById('file');
        const fileInfo = document.querySelector('.file-info');
        const uploadBtn = document.getElementById('uploadBtn');

        if (fileInput) fileInput.value = '';
        if (fileInfo) fileInfo.style.display = 'none';
        if (uploadBtn) uploadBtn.disabled = true;
    }

    setupAdvancedDragDrop() {
        const uploadArea = document.querySelector('.upload-area');
        if (!uploadArea) return;

        let dragCounter = 0;

        uploadArea.addEventListener('dragenter', (e) => {
            e.preventDefault();
            dragCounter++;
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dragCounter--;
            if (dragCounter === 0) {
                uploadArea.classList.remove('dragover');
            }
        });

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            dragCounter = 0;
            uploadArea.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const fileInput = document.getElementById('file');
                if (fileInput) {
                    fileInput.files = files;
                    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        });
    }

    setupActionButtons() {
        // Кнопка очистки файла
        document.addEventListener('click', (e) => {
            if (e.target.closest('.clear-file-btn')) {
                this.clearFile();
            }
        });

        // Кнопки экспорта графиков
        document.addEventListener('click', (e) => {
            if (e.target.closest('.export-chart-btn')) {
                const chartId = e.target.getAttribute('data-chart-id');
                this.exportChart(chartId);
            }
        });
    }

    setupProgressTracking() {
        // Отслеживание прогресса анализа
        if (window.location.pathname.includes('/analyze/')) {
            this.trackAnalysisProgress();
        }
    }

    trackAnalysisProgress() {
        const steps = [
            'Загрузка файла...',
            'Парсинг данных...',
            'Извлечение текста...',
            'Анализ слов...',
            'Создание графиков...',
            'Генерация отчета...'
        ];

        let currentStep = 0;
        const progressInterval = setInterval(() => {
            if (currentStep < steps.length) {
                this.updateProgressStep(currentStep, steps[currentStep]);
                currentStep++;
            } else {
                clearInterval(progressInterval);
            }
        }, 1500);
    }

    updateProgressStep(stepIndex, stepText) {
        const stepElement = document.getElementById(`step${stepIndex + 1}`);
        if (stepElement) {
            // Завершаем предыдущий шаг
            if (stepIndex > 0) {
                const prevStep = document.getElementById(`step${stepIndex}`);
                if (prevStep) {
                    prevStep.innerHTML = `<i class="fas fa-check-circle me-2 text-success"></i><span>${prevStep.textContent.trim()}</span>`;
                    prevStep.classList.add('completed');
                }
            }

            // Активируем текущий шаг
            stepElement.innerHTML = `<i class="fas fa-spinner fa-spin me-2 text-primary"></i><span>${stepText}</span>`;
            stepElement.classList.remove('text-muted');
        }

        // Обновляем прогресс-бар
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            const progress = ((stepIndex + 1) / 6) * 100;
            progressBar.style.width = `${progress}%`;
        }
    }

    exportChart(chartId) {
        if (typeof Plotly !== 'undefined' && document.getElementById(chartId)) {
            const filename = `telegram_analysis_${chartId}_${new Date().toISOString().slice(0, 10)}`;

            Plotly.downloadImage(chartId, {
                format: 'png',
                width: 1200,
                height: 600,
                filename: filename
            }).then(() => {
                this.showSuccess('График успешно экспортирован!');
            }).catch((error) => {
                this.showError('Ошибка при экспорте графика');
                console.error('Export error:', error);
            });
        }
    }

    initializeAnimations() {
        // Аним��ция появления элементов при скролле
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Наблюдаем за элементами для анимации
        document.querySelectorAll('.card, .chart-container').forEach(el => {
            observer.observe(el);
        });
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'danger');
    }

    showNotification(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show animate-in`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('main .container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);

            // Автоматически скрываем уведомление через 5 секунд
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.classList.remove('show');
                    setTimeout(() => {
                        if (alertDiv.parentNode) {
                            alertDiv.remove();
                        }
                    }, 150);
                }
            }, 5000);
        }
    }

    // API методы
    async loadAllReports() {
        try {
            const response = await fetch('/api/reports');
            const reports = await response.json();
            return reports;
        } catch (error) {
            this.showError('Ошибка загрузки отчетов');
            console.error('Error loading reports:', error);
            return [];
        }
    }

    async downloadReport(analysisId) {
        try {
            const response = await fetch(`/download/${analysisId}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `telegram_analysis_${analysisId}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                this.showSuccess('Отчет успешно скачан!');
            } else {
                throw new Error('Ошибка скачивания');
            }
        } catch (error) {
            this.showError('Ошибка при скачивании отчета');
            console.error('Download error:', error);
        }
    }
}

// Инициализация приложения
let telegramApp;
document.addEventListener('DOMContentLoaded', function() {
    telegramApp = new TelegramAnalyzerApp();
});

// Глобальные функции для обратной совместимости
function loadReports() {
    if (telegramApp) {
        telegramApp.loadAllReports().then(reports => {
            console.log('Загружены отчеты:', reports);
            // Здесь можно добавить отображение модального окна со списком отчетов
        });
    }
}

function showFileInfo(input) {
    if (telegramApp && input.files && input.files[0]) {
        telegramApp.handleFileSelect({ target: input });
    }
}

function clearFile() {
    if (telegramApp) {
        telegramApp.clearFile();
    }
}
