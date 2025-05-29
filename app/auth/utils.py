from wtforms.validators import ValidationError
from werkzeug.security import generate_password_hash
from app.models import User
from app.database import session_scope
from sqlalchemy.exc import SQLAlchemyError, DatabaseError


class UserDoesNotExistError(Exception):
    """Пользователь не существует"""
    pass


class DatabaseOperationError(Exception):
    """Ошибка операций с БД"""
    pass


class DataAccessError(Exception):
    """Ошибка доступа к данным"""
    pass


class ServiceError(Exception):
    """Общая ошибка сервиса"""
    pass


class AuthService:
    @staticmethod
    def validate_phone(form, field):
        """Валидация номера телефона"""
        try:
            with session_scope() as session:
                user = session.query(User).filter_by(phone=field.data).first()
                if not user:
                    raise ValidationError('Пользователя с таким номером телефона не существует')
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса книг") from error

    @staticmethod
    def check_user_by_phone(form, field):
        """Проверка отсутствия номера телефона в модели User"""
        try:
            with session_scope() as db_session:
                user_by_phone = db_session.query(User).filter_by(phone=field.data).first()
                if user_by_phone:
                    raise ValidationError('Пользователь с таким номером телефона уже существует')
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса книг") from error

    @staticmethod
    def check_user_by_email(form, field):
        """Проверка отсутствия адреса электронной почты в модели User"""
        try:
            with session_scope() as db_session:
                user_by_email = db_session.query(User).filter_by(email=field.data).first()
                if user_by_email:
                    raise ValidationError('Пользователь с таким адресом электронной почты уже существует')
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса книг") from error

    @staticmethod
    def add_user(name, surname, email, phone, password):
        """Добавляет пользователя в модель User"""
        try:
            with session_scope() as db_session:
                user = User(name=name,
                            surname=surname,
                            email=email,
                            phone=phone,
                            password_hash=generate_password_hash(password))
                db_session.add(user)
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса книг") from error

    @staticmethod
    def update_password(user_id, new_password):
        """Обновление пароля"""
        try:
            with session_scope() as db_session:
                user = db_session.query(User).get(user_id)
                user.password_hash = generate_password_hash(new_password)
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса книг") from error

