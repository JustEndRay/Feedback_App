# Конфігурація додатку для різних середовищ

import os

# Базова конфігурація
class Config:
    # Секретний ключ для підпису сесій та CSRF токенів
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mysecretkey')
    # Вимикаємо відстеження змін об'єктів SQLAlchemy для оптимізації
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # URI підключення до бази даних -
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://feedback_user:feedback_password@db:5432/feedback')

# Конфігурація для розробки
class DevelopmentConfig(Config):
    DEBUG = True  # Увімкнено режим налагодження
    # Наслідуємо правильний DATABASE_URI з Config

# Конфігурація для продакшн
class ProductionConfig(Config):
    DEBUG = False  # Вимкнено режим налагодження для безпеки
    # Наслідуємо правильний DATABASE_URI з Config

# Словник конфігурацій для вибору за ключем
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}