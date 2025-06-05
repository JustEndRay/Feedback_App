# Маршрути (URL обробники) додатку

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import User, Feedback
from flask_login import login_user, current_user, login_required, logout_user
from app.forms import LoginForm, FeedbackForm
from werkzeug.security import check_password_hash

# Створюємо Blueprint для організації маршрутів
main = Blueprint('main', __name__)


# Головна сторінка з формою відгуку
@main.route('/')
def index():
    form = FeedbackForm()
    return render_template('index.html', form=form)


# Обробка відправки відгуку
@main.route('/feedback', methods=['POST'])
def submit_feedback():
    form = FeedbackForm(request.form)
    if form.validate():
        try:
            feedback = Feedback(
                name=form.name.data,
                email=form.email.data,
                content=form.content.data
            )
            db.session.add(feedback)
            db.session.commit()
            flash('Ваш відгук було успішно надіслано!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Помилка при збереженні відгуку. Спробуйте ще раз.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('main.index'))


# Сторінка входу для адміністратора
@main.route('/login', methods=['GET', 'POST'])
def login():
    # Якщо користувач вже увійшов, перенаправляємо на панель
    if current_user.is_authenticated:
        return redirect(url_for('main.feedback_page'))

    form = LoginForm()
    if form.validate_on_submit():
        # Знаходимо користувача за ім'ям
        user = User.query.filter_by(username=form.username.data).first()
        # Перевіряємо пароль
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)  # Створюємо сесію
            flash('Успішний вхід', 'success')
            return redirect(url_for('main.feedback_page'))
        else:
            flash('Невірний логін або пароль', 'danger')

    return render_template('login.html', form=form)


# Вихід з системи
@main.route('/logout')
@login_required  # Тільки для авторизованих користувачів
def logout():
    logout_user()  # Видаляємо сесію
    flash('Ви вийшли з акаунту', 'info')
    return redirect(url_for('main.index'))


# Панель адміністратора з відгуками
@main.route('/feedback_page')
@login_required  # Тільки для авторизованих користувачів
def feedback_page():
    # Отримуємо номер сторінки з параметрів URL
    page = request.args.get('page', 1, type=int)

    # Отримуємо відгуки з пагінацією (10 на сторінку)
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    # Рахуємо загальну кількість відгуків
    total_feedbacks = Feedback.query.count()

    return render_template('feedback_page.html', feedbacks=feedbacks, total_feedbacks=total_feedbacks)


# Ендпоінт для перевірки здоров'я додатку
@main.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200