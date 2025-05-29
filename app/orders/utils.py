from app.database import session_scope
from app.models import StoreAddress, Order, OrderItem, CartItem, Book, OrderStatusEnum
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, DatabaseError


class OrderService:
    @staticmethod
    def store_address_to_string(store_address):
        """Получение адреса магазины в виде строки"""
        try:
            return store_address['store_address']
        except (KeyError, TypeError) as e:
            raise ValueError("Некорректный формат адреса магазина") from e

    @staticmethod
    def order_to_dict(order):
        """Преобразование заказа в словарь"""
        try:
            return {
                'id': order.id,
                'user_id': order.user_id,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'status': order.status.display_name,
                'delivery_method': order.delivery_method.display_name,
                'address': order.address
            }
        except AttributeError as e:
            raise ValueError("Некорректный объект заказа") from e

    @staticmethod
    def get_order_by_id(order_id):
        """Получение заказа по id заказа в виде словаря"""
        try:
            with session_scope() as db_session:
                order = db_session.query(Order).get(order_id)
                if not order:
                    raise ValueError(f'Заказ с id {order_id} не найден')
                return OrderService.order_to_dict(order)
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса") from error

    @staticmethod
    def users_orders_to_dict(user_id):
        """Получение всех заказов пользователя по его id"""
        try:
            with session_scope() as db_session:
                users_orders = db_session.query(Order).filter_by(user_id=user_id).all()
                result = sorted((OrderService.order_to_dict(order) for order in users_orders), key=lambda item: item['id'], reverse=True)
                return result
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса") from error

    @staticmethod
    def create_order(user_id, address, delivery_method):
        """Создание записи о заказе в модели Order"""
        try:
            with session_scope() as db_session:
                now = datetime.now().astimezone()

                new_order = Order(
                    user_id=user_id,
                    address=address,
                    delivery_method=delivery_method,
                    created_at=now,
                    updated_at=now
                )
                db_session.add(new_order)
                db_session.commit()
                return new_order
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса") from error

    @staticmethod
    def create_order_item(order_id, book_id, quantity, price, user_id):
        """Создание записи о единицах товара в модели OrderItem"""
        try:
            with session_scope() as db_session:
                new_order_item = OrderItem(order_id=order_id,
                                           book_id=book_id,
                                           quantity=quantity,
                                           price=price)
                db_session.add(new_order_item)
                item_to_reduce = db_session.query(Book).get(book_id)
                item_to_reduce.quantity -= new_order_item.quantity
                cart_items = db_session.query(CartItem).filter(CartItem.book_id == book_id, CartItem.user_id != user_id).all()
                print(cart_items)
                for item in cart_items:
                    if item.quantity > item_to_reduce.quantity:
                        item.quantity = item_to_reduce.quantity
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса") from error

    @staticmethod
    def get_last_order(user_id):
        """Получение последнего заказа пользователя из модели Order"""
        try:
            with session_scope() as db_session:
                last_order = db_session.query(Order).filter_by(user_id=user_id).order_by(Order.created_at.desc()).first()
                return OrderService.order_to_dict(last_order) if last_order else None
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса") from error

    @staticmethod
    def delete_cart_item(item_id):
        """Удаление товара из корзины"""
        try:
            with session_scope() as db_session:
                item_to_delete = db_session.query(CartItem).get(item_id)
                db_session.delete(item_to_delete)
                db_session.commit()
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса") from error

    @staticmethod
    def get_store_addresses():
        """Получение всех адресов из модели StoreAddress"""
        try:
            with session_scope() as db_session:
                all_addresses = db_session.query(StoreAddress).all()
                return [{
                    'id': address.id,
                    'store_address': address.store_address
                } for address in all_addresses]
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса") from error

    @staticmethod
    def order_item_to_dict(order_item):
        """Преобразование единицы заказа в словарь"""
        if not order_item:
            raise ValueError("Товар не найден в заказе")
        try:
            return {
                'id': order_item.id,
                'order_id': order_item.id,
                'book_id': order_item.book_id,
                'quantity': order_item.quantity,
                'price': float(order_item.price),
                'title': order_item.book.title,
                'author': order_item.book.author,
                'cover': order_item.book.cover
            }
        except AttributeError as e:
            raise ValueError(f"Некорректный объект товара: {e}") from e
        except TypeError as e:
            raise ValueError(f"Ошибка в данных товара: {e}") from e

    @staticmethod
    def get_order_items_in_order(order_id):
        """Получение всех единиц товара в заказе"""
        try:
            with session_scope() as db_session:
                order_items = db_session.query(OrderItem).filter_by(order_id=order_id).all()
                return [OrderService.order_item_to_dict(order_item) for order_item in order_items]
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса") from error

    @staticmethod
    def time_to_string(time_obj):
        """Преобразование времени в строку"""
        try:
            if not isinstance(time_obj, datetime):
                raise ValueError("Должен быть передан объект datetime")

            result = time_obj.strftime('%d-%m-%Y %H:%M')

            return result

        except ValueError as e:
            raise ValueError(f"Ошибка значения времени: {str(e)}") from e
        except TypeError as e:
            raise TypeError(f"Неподдерживаемый тип времени: {str(e)}") from e
        except AttributeError as e:
            raise AttributeError(f"Отсутствует необходимый атрибут: {str(e)}") from e
        except Exception as e:
            raise ServiceError(f"Ошибка преобразования времени: {str(e)}") from e

    @staticmethod
    def update_order_status(order_id, status):
        """Обновление статуса заказа"""
        try:
            with session_scope() as db_session:
                order = db_session.query(Order).get(order_id)
                if not order:
                    raise ValueError('Заказ не найден')
                try:
                    order.status = OrderStatusEnum(status)
                except ValueError:
                    raise ValueError(f'Неверный статус заказа. Допустимые значения: {[e.value for e in OrderStatusEnum]}')

                db_session.commit()
        except DatabaseError as db_error:
            raise DatabaseOperationError("Ошибка при работе с базой данных") from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError("Ошибка доступа к данным") from sql_error
        except Exception as error:
            raise ServiceError("Внутренняя ошибка сервиса") from error


class DatabaseOperationError(Exception):
    """Ошибка операций с БД"""
    pass


class DataAccessError(Exception):
    """Ошибка доступа к данным"""
    pass


class ServiceError(Exception):
    """Общая ошибка сервиса"""
    pass