# Використовуємо офіційний Python 3.11 slim образ як базовий
FROM python:3.11-slim

# Встановлюємо необхідні системні пакети
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Створюємо непривілейованого користувача для безпеки
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо та встановлюємо Python залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код додатку
COPY . .

# Змінюємо власника файлів на appuser
RUN chown -R appuser:appuser /app

# Переключаємося на непривілейованого користувача
USER appuser

# Встановлюємо змінні середовища Flask
ENV FLASK_APP=run.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Відкриваємо порт
EXPOSE 5000

# Команда запуску додатку
CMD ["python", "run.py"]