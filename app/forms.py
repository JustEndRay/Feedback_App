# Форми для веб-додатку з валідацією

from wtforms import StringField, EmailField, TextAreaField, PasswordField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, NumberRange
from flask_wtf import FlaskForm


# Форма для відправки відгуку
class FeedbackForm(FlaskForm):
    # Поле для імені користувача
    name = StringField('Ваше ім\'я', validators=[DataRequired()])
    # Поле для електронної пошти
    email = StringField('Ваш Email', validators=[DataRequired(), Email(message='Введіть коректний email')])
    # Текстове поле для відгуку
    content = TextAreaField('Ваш відгук', validators=[DataRequired()])

    # Кнопка для відправки форми
    submit = SubmitField('Відправити')


# Форма для входу адміністратора
class LoginForm(FlaskForm):
    # Поле для імені користувача
    username = StringField('Ім\'я користувача', validators=[DataRequired()])
    # Поле для пароля (приховане)
    password = PasswordField('Пароль', validators=[DataRequired()])
    # Кнопка для входу
    submit = SubmitField('Увійти')