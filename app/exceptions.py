class DatabaseOperationError(Exception):
    """Ошибка операций с БД"""


class DataAccessError(Exception):
    """Ошибка доступа к данным"""


class ServiceError(Exception):
    """Общая ошибка сервиса"""


class UserDoesNotExistError(Exception):
    """Пользователь не существует"""


class BookNotFoundError(Exception):
    """Книга не найдена в БД"""


class ReviewExistsError(Exception):
    """Проверка наличия отзыва от пользователя"""


class BooksNotFoundError(Exception):
    """Книги не найдены в БД"""









