from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired, Length, Regexp


class CodeForm(FlaskForm):
    code = StringField(
        label='Введите код, полученный по смс',
        validators=[
            InputRequired(message='Введите код'),
            Length(4, 4, message='Код содержит 3 цифры')
        ]
    )
    submit = SubmitField(label='Подтвердить оплату')


class CardDetailsForm(FlaskForm):
    card_number = StringField(
        label='Номер карты',
        validators=[
            InputRequired(message='Введите номер карты'),
            Length(16, 16, message='Номер карты содержит 16 цифр'),
            Regexp(r'^(?:\d{4}[ -]?){3}\d{4}$', message='Неверный формат номера карты')
        ]
    )
    card_date = StringField(
        label='Срок действия карты',
        validators=[
            InputRequired(message='Введите срок действия карты'),
            Length(5, 5, message='Срок действия карты содержит 5 символов'),
            Regexp(r'\b(0[1-9]|1[0-2])/\d{2}\b', message='Неверный формат срока действия')
        ]
    )
    card_owner = StringField(
        label='Владелец карты',
        validators=[
            InputRequired(message='Введите фамилию и имя владельца карты'),
            Regexp(r'\b[A-Za-z]{2,20}\s[A-Za-z]{2,20}\b', message='Неверное имя владельца')
        ]
    )
    cvv = StringField(
        label='CVV',
        validators=[
            InputRequired(message='Введите CVV-код'),
            Length(3, 3, message='CVV должен содержать 3 цифры'),
            Regexp(r'\b\d{3}\b', message='Неверный формат CVV')
        ]
    )
    submit = SubmitField(label='Получить код для оплаты')

