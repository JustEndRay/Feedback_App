#!/usr/bin/env python3

import os
import sys
from werkzeug.security import generate_password_hash

# Додаємо поточну директорію до PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User


def create_admin_user():
    # Створюємо контекст додатку
    app = create_app()

    with app.app_context():
        try:
            # Перевіряємо чи існує адміністратор
            admin_user = User.query.filter_by(username='admin').first()

            if not admin_user:
                # Створюємо нового адміністратора з паролем
                password = os.getenv('ADMIN_PASSWORD', '123456789')
                admin_user = User(
                    username='admin',
                    email='admin@feedback-app.com',
                    password_hash=generate_password_hash(password)
                )
                db.session.add(admin_user)
                db.session.commit()
                print(f"✅ Адміністратора успішно створено!")
                print(f"👤 Ім'я користувача: admin")
                print(f"🔑 Пароль: {password}")
            else:
                print("ℹ️ Адміністратор вже існує")
        except Exception as e:
            print(f"❌ Помилка при створенні адміністратора: {e}")
            db.session.rollback()
            sys.exit(1)


if __name__ == "__main__":
    create_admin_user()