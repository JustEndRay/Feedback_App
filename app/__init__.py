# Ініціалізація Flask додатку та його розширень

from flask import Flask
from flask_sqlalchemy import SQLAlchemy      # ORM для роботи з базою даних
from flask_migrate import Migrate            # Міграції бази даних
from flask_login import LoginManager         # Управління сесіями користувачів
import os

from .config import Config  # Імпортуємо конфігурацію з поточної папки app

# Ініціалізуємо розширення Flask
db = SQLAlchemy()           # Об'єкт бази даних
migrate = Migrate()         # Об'єкт міграцій
login_manager = LoginManager()  # Менеджер аутентифікації

# Функція для завантаження користувача з сесії
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

# Фабрична функція для створення додатку
def create_app(config_class=Config):
    app = Flask(__name__)

    # Визначаємо конфігурацію на основі змінної середовища
    config_name = os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config_class)

    # Ініціалізуємо розширення з додатком
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # Сторінка входу за замовчуванням

    # Ініціалізація метрик (закоментовано)
    # metrics = init_metrics(app)

    # Реєструємо blueprints (модулі маршрутів)
    from app.routes import main
    app.register_blueprint(main)

    # Налаштування повідомлень для логіну
    login_manager.login_message = 'Будь ласка, увійдіть для доступу до цієї сторінки.'
    login_manager.login_message_category = 'info'

    # Ендпоінт перевірки здоров'я системи
    @app.route('/health')
    def health_check():
        try:
            # Перевірка підключення до бази даних
            db.session.execute('SELECT 1')
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'

        return {
            'status': 'healthy',
            'database': db_status
        }

    return app

# Експортуємо db для використання в інших модулях
__all__ = ['db']