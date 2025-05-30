import json
from app.database import session_scope, init_db
from app.models import Book, Review, User, StoreAddress, Order, OrderStatusEnum, OrderMethodEnum, OrderItem
from sqlalchemy.exc import DatabaseError
from pathlib import Path
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random


class DatabaseInitializationError(Exception):
    """Ошибка инициализации базы данных"""
    pass


class DataValidationError(Exception):
    """Ошибка валидации данных"""
    pass


def ensure_db_exists():
    """Создает БД и папку instance если их нет"""
    try:
        db_path = Path('app/instance/bookstore.db')

        db_path.parent.mkdir(exist_ok=True)

        init_file = db_path.parent / '__init__.py'
        if not init_file.exists():
            init_file.touch()

        if not db_path.exists():
            init_db()
    except PermissionError as e:
        raise DatabaseInitializationError(f"Ошибка прав доступа при создании БД: {e}")
    except Exception as e:
        raise DatabaseInitializationError(f"Неожиданная ошибка при создании БД: {e}")


def init_books():
    """Заполнит таблицу с книгами"""
    try:
        json_path = Path('app/files/books_catalog.json')

        if not json_path.exists():
            raise FileNotFoundError(f"Файл {json_path} не найден")

        with session_scope() as db_session:
            if db_session.query(Book).first():
                return

            try:
                with open('app/files/books_catalog.json', 'r', encoding='utf-8') as f:
                    books_data = json.load(f)

                for item in books_data:
                    try:
                        book = Book(title=item['title'],
                                    author=item['author'],
                                    price=float(item['price']),
                                    genre=item['genre'],
                                    cover='img/no_pic.png',
                                    description=item['description'],
                                    pages=int(item['pages']),
                                    rating=float(item['rating']),
                                    year=int(item['year']),
                                    quantity=int(item['quantity'])
                                    )
                        db_session.add(book)
                    except (KeyError, ValueError, TypeError) as e:
                        raise DataValidationError(f"Ошибка в данных книги: {e}")

            except json.JSONDecodeError as e:
                raise DataValidationError(f"Ошибка в формате JSON: {e}")
    except DatabaseError as db_error:
        raise DatabaseInitializationError(f"Ошибка базы данных: {db_error}")
    except Exception as e:
        raise DatabaseInitializationError(f"Неожиданная ошибка при заполнении книг: {e}")


def init_reviews():
    """Заполнит таблицу с отзывами"""
    try:
        json_path = Path('app/files/first_reviews.json')

        if not json_path.exists():
            raise FileNotFoundError(f"Файл {json_path} не найден")
        with session_scope() as db_session:
            if db_session.query(Review).first():
                return

            try:
                with open('app/files/first_reviews.json', 'r', encoding='utf-8') as f:
                    reviews_data = json.load(f)
                for item in reviews_data:
                    try:
                        review = Review(review=item['review'],
                                        user_id=item['user_id'],
                                        book_id=item['book_id'],
                                        rating=item['rating']
                                    )
                        db_session.add(review)
                    except (KeyError, ValueError) as e:
                        raise DataValidationError(f"Ошибка в данных отзыва: {e}")
            except json.JSONDecodeError as e:
                raise DataValidationError(f"Ошибка в формате JSON: {e}")

    except DatabaseError as db_error:
        raise DatabaseInitializationError(f"Ошибка базы данных: {db_error}")
    except Exception as e:
        raise DatabaseInitializationError(f"Неожиданная ошибка при заполнении отзывов: {e}")


def init_users():
    """Заполнит таблицу с пользователями"""
    users = [
        {
             'name': 'Jane',
             'surname': 'Doe',
             'email': 'janed@mail.ru',
             'phone': '89384762941',
             'password': '123456789'
        },
        {
             'name': 'John',
             'surname': 'Dare',
             'email': 'john@mail.ru',
             'phone': '89384762942',
             'password': '12345678'
        },
        {
             'name': 'Liza',
             'surname': 'Bo',
             'email': 'liza@mail.ru',
             'phone': '89384762943',
             'password': '123456789'
        },
        {
             'name': 'Alina',
             'surname': 'Petrova',
             'email': 'petrova@mail.ru',
             'phone': '89384762944',
             'password': '123456789'
        },
        {
             'name': 'Masha',
             'surname': 'Shevchenko',
             'email': 'mashka@mail.ru',
             'phone': '89384762945',
             'password': '123456789'
        },
        {
            'name': 'Lena',
            'surname': 'Poleno',
            'email': 'lena@mail.ru',
            'phone': '89384762946',
            'password': '123456789'
        },
        {
            'name': 'Igor',
            'surname': 'Petrov',
            'email': 'petrov@mail.ru',
            'phone': '89384762947',
            'password': '123456789'
        },
        {
            'name': 'Nikita',
            'surname': 'Borisov',
            'email': 'borya@mail.ru',
            'phone': '89384762948',
            'password': '123456789'
        },
        {
            'name': 'Dima',
            'surname': 'Book',
            'email': 'books@mail.ru',
            'phone': '89384762949',
            'password': '123456789'
        },
        {
            'name': 'Nick',
            'surname': 'Mitin',
            'email': 'mitin@mail.ru',
            'phone': '89384762950',
            'password': '123456789'
        },
    ]
    try:
        with session_scope() as db_session:
            if db_session.query(User).first():
                return
            for user in users:
                try:
                    if not db_session.query(User).filter_by(email=user['email']).first():
                        hashed_password = generate_password_hash(user['password'])
                        db_session.add(User(
                            name=user['name'],
                            surname=user['surname'],
                            email=user['email'],
                            phone=user['phone'],
                            password_hash=hashed_password
                        ))
                except (KeyError, ValueError) as e:
                    raise DataValidationError(f"Ошибка в данных пользователя: {e}")
    except DatabaseError as db_error:
        raise DatabaseInitializationError(f"Ошибка базы данных: {db_error}")
    except Exception as e:
        raise DatabaseInitializationError(f"Неожиданная ошибка при заполнении пользователей: {e}")


store_addresses = [
    {
        'city': 'Москва',
        'street': 'Кржижановского',
        'house': 10,
        'building': 1
    },
    {
        'city': 'Москва',
        'street': 'Шарикоподшипниковская',
        'house': 6,
        'building': 3,
    },
    {
        'city': 'Москва',
        'street': 'Парковая',
        'house': 23,
        'building': 1,
    },
    {
        'city': 'Москва',
        'street': 'Тверская',
        'house': 43,
        'building': 1,
    },
    {
        'city': 'Москва',
        'street': 'Новослободская',
        'house': 30,
        'building': 2,
    },
    {
        'city': 'Москва',
        'street': 'Проспект Мира',
        'house': 14,
        'building': 2,
    },
    {
        'city': 'Москва',
        'street': 'Варшавское шоссе',
        'house': 36,
        'building': 1,
    },
    {
        'city': 'Москва',
        'street': 'Каширское шоссе',
        'house': 60,
        'building': 4,
    },
    {
        'city': 'Москва',
        'street': 'Таганская',
        'house': 5,
        'building': 1,
    },
    {
        'city': 'Москва',
        'street': 'Ленинский проспект',
        'house': 20,
        'building': 1,
    }
]


def init_store_address():
    """Заполнит таблицу с адресами магазина"""
    try:
        with session_scope() as db_session:
            if db_session.query(StoreAddress).first():
                return
            for store_address in store_addresses:
                try:
                    full_address = (
                        f'г. {store_address["city"]}, '
                        f'ул. {store_address["street"]}, '
                        f'д. {store_address["house"]}, '
                        f'к. {store_address["building"]}'
                    )
                    if not db_session.query(StoreAddress).filter_by(store_address=full_address).first():
                        db_session.add(StoreAddress(store_address=full_address))
                except (KeyError, ValueError) as e:
                    raise DataValidationError(f"Ошибка в данных адреса: {e}")
    except DatabaseError as db_error:
        raise DatabaseInitializationError(f"Ошибка базы данных: {db_error}")
    except Exception as e:
        raise DatabaseInitializationError(f"Неожиданная ошибка при заполнении адресов: {e}")


def create_orders():
    """Заполнит таблицу с заказами"""
    try:
        today = datetime.now().astimezone()
        last_week_monday = (today - timedelta(days=today.weekday() + 7))
        orders = []

        with session_scope() as db_session:
            for _ in range(30):
                try:
                    user_id = random.randint(1, 10)
                    days_plus = random.randint(0, 7)
                    created_at = (last_week_monday + timedelta(days=days_plus))
                    days_difference = random.randint(0, (today - created_at).days)
                    status = random.choice(list(OrderStatusEnum))
                    updated_at = created_at if status == 'new' else (created_at + timedelta(days=days_difference))
                    delivery_method = random.choice(list(OrderMethodEnum))

                    address = ''
                    if delivery_method == 'pickup':
                        index = random.randrange(len(store_addresses))
                        address = (f'г. {store_addresses[index]["city"]}, '
                                   f'ул. {store_addresses[index]["street"]}, '
                                   f'д. {store_addresses[index]["house"]}, '
                                   f'к. {store_addresses[index]["building"]}')
                    elif delivery_method == 'door':
                        address = (f'г. {store_addresses[random.randrange(len(store_addresses))]["city"]}, '
                                   f'ул. {store_addresses[random.randrange(len(store_addresses))]["street"]}, '
                                   f'д. {store_addresses[random.randrange(len(store_addresses))]["house"]}, '
                                   f'к. {store_addresses[random.randrange(len(store_addresses))]["building"]}')
                    full_address = ' '.join(address)

                    order = Order(
                        user_id=user_id,
                        created_at=created_at,
                        updated_at=updated_at,
                        status=status,
                        delivery_method=delivery_method,
                        address=full_address
                    )
                    db_session.add(order)
                    orders.append(order)
                except (ValueError, IndexError) as e:
                    raise DataValidationError(f"Ошибка в данных заказа: {e}")

            db_session.commit()

            return sorted(order.id for order in orders)
    except DatabaseError as db_error:
        raise DatabaseInitializationError(f"Ошибка базы данных: {db_error}")
    except Exception as e:
        raise DatabaseInitializationError(f"Неожиданная ошибка при создании заказов: {e}")


def create_order_item(created_orders_ids):
    """Создает таблицу с товарами в заказах"""
    try:
        with session_scope() as db_session:
            for order_id in created_orders_ids:
                try:
                    items_count = random.randint(1, 10)

                    for _ in range(items_count):
                        book_id = random.randint(1, 100)
                        quantity = random.randint(1, 3)
                        price = db_session.query(Book).filter_by(id=book_id).first().price

                        order_item = OrderItem(
                            order_id=order_id,
                            book_id=book_id,
                            quantity=quantity,
                            price=price
                        )
                        db_session.add(order_item)
                except (ValueError, AttributeError) as e:
                    raise DataValidationError(f"Ошибка в данных элемента заказа: {e}")
    except DatabaseError as db_error:
        raise DatabaseInitializationError(f"Ошибка базы данных: {db_error}")
    except Exception as e:
        raise DatabaseInitializationError(f"Неожиданная ошибка при создании элементов заказов: {e}")


def init_orders():
    """Заполнит таблицу с заказами и содержанием заказов"""
    try:
        with session_scope() as db_session:
            if db_session.query(Order).first():
                return
        created_orders_ids = create_orders()
        create_order_item(created_orders_ids)
    except DatabaseInitializationError:
        raise
    except Exception as e:
        raise DatabaseInitializationError(f"Неожиданная ошибка при инициализации заказов: {e}")




