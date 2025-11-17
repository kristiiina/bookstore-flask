from wtforms.validators import ValidationError
from werkzeug.security import generate_password_hash
from app.exceptions import (DatabaseOperationError,
                            DataAccessError,
                            ServiceError,
                            BooksNotFoundError,
                            BookNotFoundError,
                            ReviewExistsError)
from app.models import User, Book, Review, CartItem, OrderItem, Order, StoreAddress, OrderStatusEnum
from app.database import session_scope
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
import re
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import joinedload


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


class BookService:
    @staticmethod
    def book_to_dict(book):
        """Получает книгу по объекту из БД"""
        if not book:
            raise ValueError('Книга не найдена')
        try:
            quantity_in_orders = sum(item.quantity for item in book.in_orders) if hasattr(book, 'in_orders') else 0
            return {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'price': book.price,
                'genre': book.genre,
                'cover': book.cover,
                'description': book.description,
                'pages': book.pages,
                'rating': book.rating,
                'year': book.year,
                'quantity': book.quantity,
                'quantity_in_orders': quantity_in_orders
            }
        except AttributeError as e:
            raise ValueError(f'Некорректный объект книги: {e}') from e
        except TypeError as e:
            raise ValueError(f'Ошибка в данных книги: {e}') from e

    @staticmethod
    def review_to_dict(review):
        """Преобразование отзыва в словарь"""
        if not review:
            raise ValueError('Отзыв не найден')
        try:
            return {
                'id': review.id,
                'review': review.review,
                'user_id': review.user_id,
                'book_id': review.book_id,
                'rating': review.rating,
                'user': f'{review.user.name} {review.user.surname[0]}.',
                'books': review.book.title
            }
        except AttributeError as e:
            raise ValueError(f'Некорректный объект отзыва: {str(e)}')

    @staticmethod
    def get_all_books():
        """Получает все книги из БД в виде списка со словарями"""
        try:
            with session_scope() as db_session:
                all_books = db_session.query(Book).all()
                if not all_books:
                    raise BooksNotFoundError('Книги не найдены')
                return [BookService.book_to_dict(book) for book in all_books]

        except DatabaseError as db_error:
                raise DatabaseOperationError('Ошибка при работе с базой данных') from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError('Ошибка доступа к данным') from sql_error
        except Exception as error:
            raise ServiceError('Внутренняя ошибка сервиса книг') from error

    @staticmethod
    def get_book_by_id(book_id):
        """Получает книгу по ID в виде словаря, вызывает BookNotFound если не найдена"""
        try:
            with session_scope() as db_session:
                book = db_session.query(Book).get(book_id)
                if not book:
                    raise BookNotFoundError(f'Книга с id {book_id} не найдена')
                return BookService.book_to_dict(book)
        except DatabaseError as db_error:
                raise DatabaseOperationError('Ошибка при работе с базой данных') from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError('Ошибка доступа к данным') from sql_error
        except Exception as error:
            raise ServiceError('Внутренняя ошибка сервиса книг') from error

    @staticmethod
    def get_books_by_genre():
        """Получение всех книг по жанру в виде словаря"""
        books = BookService.get_all_books()
        books_by_genre = dict()
        for book in books:
            book_info = {
                'id': book['id'],
                'title': book['title'],
                'author': book['author'],
                'cover': book['cover'],
                'rating': book['rating']
            }
            if book['genre'] not in books_by_genre:
                books_by_genre[book['genre']] = []
            books_by_genre[book['genre']].append(book_info)
        return books_by_genre

    @staticmethod
    def check_book_quantity(book_id):
        """Проверяет количество доступных экземпляров книг в БД"""
        try:
            with session_scope() as db_session:
                book = db_session.query(Book).get(book_id)
                if not book:
                    return None
                return book.quantity
        except DatabaseError as db_error:
                raise DatabaseOperationError('Ошибка при работе с базой данных') from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError('Ошибка доступа к данным') from sql_error
        except Exception as error:
            raise ServiceError('Внутренняя ошибка сервиса книг') from error

    @staticmethod
    def get_reviews_by_book_id(book_id):
        """Получает все отзывы о книге по id книги в виде словаря"""
        try:
            with session_scope() as db_session:
                reviews = db_session.query(Review).filter_by(book_id=book_id).all()
                if not reviews:
                    return []
                return [BookService.review_to_dict(review) for review in reviews]
        except DatabaseError as db_error:
            raise DatabaseOperationError('Ошибка при работе с базой данных') from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError('Ошибка доступа к данным') from sql_error
        except Exception as error:
            raise ServiceError('Внутренняя ошибка сервиса книг') from error

    @staticmethod
    def add_review(review_text, user_id, book_id, rating):
        """Добавление отзыва в БД"""
        try:
            with session_scope() as db_session:
                book = db_session.query(Book).get(book_id)
                if not book:
                    raise BookNotFoundError(f'Книга с id {book_id} не найдена')
                review = db_session.query(Review).filter_by(user_id=user_id, book_id=book_id).first()
                if review:
                    raise ReviewExistsError('Вы уже оценили эту книгу')
                new_review = Review(review=review_text,
                                    user_id=user_id,
                                    book_id=book_id,
                                    rating=rating)
                db_session.add(new_review)
                book.update_rating()
                return new_review
        except DatabaseError as db_error:
                raise DatabaseOperationError('Ошибка при работе с базой данных') from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError('Ошибка доступа к данным') from sql_error
        except Exception as error:
            raise ServiceError('Внутренняя ошибка сервиса книг') from error

    @staticmethod
    def update_cart(user_id, book_id):
        """Добавление книги в корзину"""
        try:
            with session_scope() as db_session:
                book = db_session.query(Book).get(book_id)
                if not book:
                    raise BookNotFoundError(f'Книга с id {book_id} не найдена')

                cart_item = db_session.query(CartItem).filter_by(user_id=user_id, book_id=book_id).first()
                if cart_item:
                    if cart_item.book.quantity >= cart_item.quantity + 1:
                        cart_item.quantity += 1
                        return cart_item
                    else:
                        raise ValueError('Нельзя повторно добавить в корзину этот товар')

                new_cart_item = CartItem(user_id=user_id,
                                         book_id=book_id,
                                         quantity=1)
                db_session.add(new_cart_item)
            return new_cart_item
        except DatabaseError as db_error:
                raise DatabaseOperationError('Ошибка при работе с базой данных') from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError('Ошибка доступа к данным') from sql_error
        except Exception as error:
            raise ServiceError('Внутренняя ошибка сервиса книг') from error

    @staticmethod
    def search_book(user_query):
        """Поиск книги"""
        if not user_query or len(user_query.strip()) < 2:
            raise ValueError('Слишком короткий поисковый запрос')
        user_query = user_query.lower().strip()
        try:
            all_books = BookService.get_all_books()
            if not all_books:
                return []
            result = []
            for book in all_books:
                regex_title = re.search(user_query, book['title'].lower())
                regex_author = re.search(user_query, book['author'].lower())
                if (regex_title or regex_author) and book not in result:
                    result.append(book)
            return result
        except Exception as e:
            print(f'Произошла ошибка: {e}')
            raise ServiceError(f'Ошибка поиска: {str(e)}') from e

    @staticmethod
    def get_top_books():
        """Получение ТОП-3 книг прошедшей недели"""
        today = datetime.now()
        last_week_monday = today - timedelta(days=today.weekday() + 7)
        last_week_monday = last_week_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        last_week_sunday = last_week_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)

        try:
            with session_scope() as db_session:
                orders = (
                    db_session.query(Order)
                    .options(joinedload(Order.items).joinedload(OrderItem.book))
                    .filter(
                        Order.created_at >= last_week_monday,
                        Order.created_at <= last_week_sunday
                    )
                    .all()
                )

                book_stats = defaultdict(
                    lambda: {
                        'id': None,
                        'title': None,
                        'author': None,
                        'cover': None,
                        'quantity': 0
                    }
                )

                for order in orders:
                    for item in order.items:
                        book = item.book
                        book_stats[book.id]['id'] = book.id
                        book_stats[book.id]['title'] = book.title
                        book_stats[book.id]['author'] = book.author
                        book_stats[book.id]['cover'] = book.cover
                        book_stats[book.id]['quantity'] = book.quantity

                top_books = sorted(
                    book_stats.items(),
                    key=lambda item: item[1]['quantity'],
                    reverse=True
                )[:3]

                return top_books

        except DatabaseError as db_error:
                raise DatabaseOperationError('Ошибка при работе с базой данных') from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError('Ошибка доступа к данным') from sql_error
        except Exception as error:
            raise ServiceError('Внутренняя ошибка сервиса книг') from error

    @staticmethod
    def get_top_books_by_genre():
        """Получение топ-книг по жанру"""
        try:
            with session_scope() as db_session:
                orders = db_session.query(Order).all()
                genre_stats = defaultdict(lambda: [])

                for order in orders:
                    for item in order.items:
                        book = BookService.book_to_dict(item.book)
                        genre = book['genre']
                        book_dict = {
                            'id': book['id'],
                            'title': book['title'],
                            'author': book['author'],
                            'genre': book['genre'],
                            'cover': book['cover'],
                            'quantity_in_orders': book['quantity_in_orders']}
                        if book_dict not in genre_stats[genre]:
                            genre_stats[genre].append(
                                {
                                    'id': book['id'],
                                    'title': book['title'],
                                    'author': book['author'],
                                    'genre': book['genre'],
                                    'cover': book['cover'],
                                    'quantity_in_orders': book['quantity_in_orders']}
                            )

                top_books_by_genre = {
                    genre: sorted(genre_stats[genre], key=lambda item: item['quantity_in_orders'], reverse=True)[:3]
                    for genre in genre_stats
                }

                return top_books_by_genre

        except DatabaseError as db_error:
            raise DatabaseOperationError('Ошибка при работе с базой данных') from db_error
        except SQLAlchemyError as sql_error:
            raise DataAccessError('Ошибка доступа к данным') from sql_error
        except Exception as error:
            raise ServiceError('Внутренняя ошибка сервиса книг') from error


class CartService:
    @staticmethod
    def cart_item_to_dict(cart_item):
        """Возвращает объект из cart_item в виде словаря"""
        if not cart_item:
            raise ValueError('Товар не найден в корзине')
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


class OrderService:
    @staticmethod
    def store_address_to_string(store_address):
        """Получение адреса магазина в виде строки"""
        try:
            return store_address['store_address']
        except (KeyError, TypeError) as e:
            raise ValueError('Некорректный формат адреса магазина') from e

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
            raise ValueError('Некорректный объект заказа') from e

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


