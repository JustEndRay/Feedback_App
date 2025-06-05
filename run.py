# Точка входу для запуску Flask додатку

from app import create_app
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Gauge
from app.models import Feedback
from app import db

# Створюємо екземпляр додатку
app = create_app()
metrics = PrometheusMetrics(app)

# Add default metrics
metrics.info('app_info', 'Application info', version='1.0.0')

feedback_count_gauge = Gauge('feedback_count', 'Total number of feedbacks')

@app.before_request
def update_feedback_count():
    try:
        count = db.session.query(Feedback).count()
        feedback_count_gauge.set(count)
    except Exception:
        pass  # Можна додати логування помилок

@app.route('/health')
# Ендпоінт для перевірки здоров'я додатку
def health():
    return 'OK', 200

# Запускаємо додаток, якщо файл запущено напряму
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)