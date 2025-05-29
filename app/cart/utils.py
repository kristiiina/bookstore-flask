from app.database import session_scope
from app.models import CartItem
from sqlalchemy.exc import SQLAlchemyError, DatabaseError


class DatabaseOperationError(Exception):
    """Ошибка операций с БД"""
    pass


class DataAccessError(Exception):
    """Ошибка доступа к данным"""
    pass


class ServiceError(Exception):
    """Общая ошибка сервиса"""
    pass


class CartService:
    @staticmethod
    def cart_item_to_dict(cart_item):
        """Возвращает объект из cart_item в виде словаря"""
        if not cart_item:
            raise ValueError("Товар не найден в корзине")
        try:
            return {
                'id': cart_item.id,
                'user_id': cart_item.user_id,
                'book_id': cart_item.book_id,
                'quantity': cart_item.quantity,
                'store_quantity': cart_item.book.quantity,
                'title': cart_item.book.title,
                'author': cart_item.book.author,
                'price': float(cart_item.book.price),
                'cover': cart_item.book.cover
            }
        except AttributeError as e:
            raise ValueError(f"Некорректный объект товара: {e}") from e
        except TypeError as e:
            raise ValueError(f"Ошибка в данных товара: {e}") from e

    @staticmethod
    def get_cart(user_id):
        """Получаем корзину пользователя по его id в виде списка словарей"""
        try:
            with session_scope() as db_session:
                db_cart = db_session.query(CartItem).filter_by(user_id=user_id).all()
                return [CartService.cart_item_to_dict(item) for item in db_cart]
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса книг") from error

    @staticmethod
    def get_available_items_from_cart(user_id):
        """Получаем доступные товары из корзины пользователя по его id"""
        try:
            with session_scope() as db_session:
                db_cart = db_session.query(CartItem).filter_by(user_id=user_id).all()
                return [CartService.cart_item_to_dict(item) for item in db_cart if item.book.quantity >= 1]
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса книг") from error

    @staticmethod
    def get_unavailable_items_from_cart(user_id):
        """Получаем недоступные товары из корзины пользователя по его id"""
        try:
            with session_scope() as db_session:
                db_cart = db_session.query(CartItem).filter_by(user_id=user_id).all()
                return [CartService.cart_item_to_dict(item) for item in db_cart if item.book.quantity == 0]
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса книг") from error

    @staticmethod
    def handle_cart_actions(item_id, action):
        """Управляем действиями пользователя в корзине: добавление и удаление единиц товара"""
        try:
            with session_scope() as db_session:
                cart_item = db_session.query(CartItem).get(item_id)
                if not cart_item:
                    raise ValueError(f'В корзине не найден товар с id {item_id}')
                if action == 'add':
                    if cart_item.book.quantity >= cart_item.quantity + 1:
                        cart_item.quantity += 1
                    else:
                        raise ValueError(
                            f'Вы не можете добавить еще один товар {cart_item.book.author} "{cart_item.book.title}" в корзину'
                        )
                elif action == 'delete':
                    cart_item.quantity -= 1
                    if cart_item.quantity <= 0:
                        db_session.delete(cart_item)
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса книг") from error

    @staticmethod
    def clear_users_cart(user_id):
        """Очищение корзины"""
        try:
            with session_scope() as db_session:
                cart = db_session.query(CartItem).filter_by(user_id=user_id).first()
                if cart:
                    db_session.query(CartItem).filter(CartItem.user_id == user_id).delete()
                    db_session.commit()
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса книг") from error


