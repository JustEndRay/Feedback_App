# Моделі бази даних

from app import db
from flask_login import UserMixin

# Модель користувача (адміністратор)
class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Назва таблиці в БД

    # Первинний ключ
    id = db.Column(db.Integer, primary_key=True)
    # Унікальне ім'я користувача
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Унікальна електронна пошта
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Хеш пароля
    password_hash = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Модель відгуку користувача
class Feedback(db.Model):
    __tablename__ = 'feedbacks'  # Назва таблиці в БД

    # Первинний ключ
    id = db.Column(db.Integer, primary_key=True)
    # Ім'я відправника відгуку
    name = db.Column(db.String(100), nullable=False)
    # Email відправника
    email = db.Column(db.String(100), nullable=False)
    # Текст відгуку
    content = db.Column(db.Text, nullable=False)
    # Дата та час створення (автоматично встановлюється)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Feedback from {self.name}>'