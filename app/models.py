from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, CheckConstraint
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text
from enum import Enum
from typing import List

Base = declarative_base()


class User(Base, UserMixin):
    """Пользователи сайта"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(length=30), nullable=False)
    surname = Column(String(length=30), nullable=False)
    email = Column(String(length=80), unique=True, nullable=False)
    phone = Column(String(length=12), unique=True, nullable=False)
    password_hash = Column(String(length=256), nullable=False)

    cart_items = relationship('CartItem', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)
    orders = relationship('Order', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)
    reviews = relationship('Review', back_populates='user')


class Book(Base):
    """Книги в магазине"""
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String(length=80), nullable=False)
    author = Column(String(length=80), nullable=False)
    price = Column(Numeric(precision=10, scale=2), nullable=False)
    genre = Column(String(length=80), nullable=False)
    cover = Column(String(length=256))
    description = Column(String(length=1000), nullable=False)
    pages = Column(Integer, nullable=False)
    rating = Column(Numeric(precision=2, scale=1), nullable=False)
    year = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)

    in_carts = relationship('CartItem', back_populates='book', passive_deletes=True)
    in_orders = relationship('OrderItem', back_populates='book', passive_deletes=True)
    reviews = relationship('Review', back_populates='book', cascade='all, delete-orphan', passive_deletes=True)

    def update_rating(self):
        reviews: List[Review] = self.reviews
        if reviews:
            total = sum(review.rating for review in reviews)
            self.rating = round(total / len(reviews), 1)


class CartItem(Base):
    """Товары в корзинах пользователей"""
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    user = relationship('User', back_populates='cart_items')
    book = relationship('Book', back_populates='in_carts')


class OrderStatusEnum(str, Enum):
    NEW = 'new'
    PAID = 'paid'
    SHIPPED = 'shipped'
    RECEIVED = 'received'

    @property
    def display_name(self):
        names = {
            'new': 'Новый',
            'paid': 'Оплачен',
            'shipped': 'Отправлен',
            'received': 'Получен'
        }
        return names[self.value]


class OrderMethodEnum(str, Enum):
    PICKUP = 'pickup'
    DOOR = 'door'

    @property
    def display_name(self):
        names = {
            'pickup': 'Самовывоз',
            'door': 'Курьером до двери'
        }
        return names[self.value]


class Order(Base):
    """Заказы пользователей"""
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True),
                        server_default=text("(datetime('now', 'localtime', 'subsec'))"),
                        nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        server_default=text("(datetime('now', 'localtime', 'subsec'))"),
                        onupdate=text("(datetime('now', 'localtime', 'subsec'))"),
                        nullable=False)
    status = Column(SQLAlchemyEnum(OrderStatusEnum), default=OrderStatusEnum.NEW, nullable=False)
    delivery_method = Column(SQLAlchemyEnum(OrderMethodEnum), nullable=False)
    address = Column(String(length=100), nullable=False)

    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan', passive_deletes=True)


class OrderItem(Base):
    """Позиции в заказах (фиксирует цену на момент заказа)"""
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='RESTRICT'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Numeric(precision=10, scale=2), nullable=False)

    order = relationship('Order', back_populates='items')
    book = relationship('Book', back_populates='in_orders')


class Review(Base):
    """Отзывы пользователей на книги"""
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    review = Column(String(length=1000), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    rating = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_between_1_and_5'),
    )

    user = relationship('User', back_populates='reviews')
    book = relationship('Book', back_populates='reviews')


class StoreAddress(Base):
    """Адреса магазинов"""
    __tablename__ = 'store_addresses'
    id = Column(Integer, primary_key=True)
    store_address = Column(String(length=500), nullable=False)











