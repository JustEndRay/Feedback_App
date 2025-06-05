#!/usr/bin/env python3

import os
import sys

# Додаємо поточну директорію до PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db


def init_database():
    # Створюємо контекст додатку
    app = create_app()

    with app.app_context():
        try:
            # Створюємо всі таблиці в базі даних
            db.create_all()
            print("✅ Таблиці бази даних успішно створено!")
        except Exception as e:
            print(f"❌ Помилка при створенні таблиць бази даних: {e}")
            sys.exit(1)


if __name__ == "__main__":
    init_database()