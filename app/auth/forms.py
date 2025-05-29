from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, Email, EqualTo, Regexp
from app.auth.utils import AuthService


class RegistrationForm(FlaskForm):
    name = StringField(
        label='Имя',
        validators=[
            InputRequired(message='Введите имя'),
            Length(max=30, min=1),
            Regexp(r'^[A-Za-zА-Яа-яЁё\- ]+$', message='Имя должно состоять из букв')
        ]
    )
    surname = StringField(
        label='Фамилия',
        validators=[
            InputRequired(message='Введите фамилию'),
            Length(max=30, min=1),
            Regexp(r'^[A-Za-zА-Яа-яЁё\- ]+$', message='Фамилия должна состоять из букв')
        ]
    )
    email = StringField(
        label='E-mail',
        validators=[
            InputRequired(message='Введите e-mail'),
            Email(),
            AuthService.check_user_by_email
        ]
    )
    phone = StringField(
        label='Телефон',
        validators=[
            InputRequired(message='Введите номер телефона'),
            Regexp(
                r'^(\+7|8)\d{10}$',
                message='Номер должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX (11 цифр)'
            ),
            AuthService.check_user_by_phone
        ]
    )
    password = PasswordField(
        label='Пароль',
        validators=[
            InputRequired(message='Введите пароль'),
            Length(min=8, max=36)
        ]
    )
    confirm_password = PasswordField(
        label='Повторите пароль',
        validators=[
            InputRequired(message='Подтвердите пароль'),
            EqualTo(fieldname='password')
        ]
    )
    submit = SubmitField(label='Зарегистрироваться')


class LoginForm(FlaskForm):
    email = StringField(
        label='Email',
        validators=[
            InputRequired(),
            Email()
        ]
    )
    password = PasswordField(
        label='Пароль',
        validators=[
            InputRequired()
        ]
    )
    submit = SubmitField('Войти')


class ResetPasswordPhoneForm(FlaskForm):
    phone = StringField(
        label='Телефон',
        validators=[
            InputRequired(message='Введите номер телефона')
        ]
    )
    submit = SubmitField(label='Далее')


class ResetPasswordCodeForm(FlaskForm):
    code = StringField(
        label='Введите код, полученный по смс',
        validators=[
            InputRequired(message='Введите код')
        ]
    )
    submit = SubmitField(label='Далее')


class ResetPasswordNewForm(FlaskForm):
    new_password = PasswordField(
        label='Пароль',
        validators=[
            InputRequired(message='Введите пароль'),
            Length(min=8, max=36)
        ]
    )
    confirm_new_password = PasswordField(
        label='Повторите пароль',
        validators=[
            InputRequired(message='Подтвердите пароль'),
            EqualTo(fieldname='new_password')
        ]
    )
    submit = SubmitField(label='Сохранить')

