from app.database import session_scope
from app.models import Book, Review, CartItem, OrderItem, Order
import re
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError, DatabaseError


class BookNotFoundError(Exception):
    """Книга не найдена в БД"""
    pass


class ReviewExistsError(Exception):
    pass


class BooksNotFoundError(Exception):
    """Книги не найдены в БД"""
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


