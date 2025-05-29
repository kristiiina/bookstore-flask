from app import app
from app.config import settings
from app.commands import ensure_db_exists, init_books, init_reviews, init_users, init_store_address, init_orders


if __name__ == '__main__':
    try:
        ensure_db_exists()
        init_books()
        init_users()
        init_reviews()
        init_store_address()
        init_orders()

        try:
            app.run(port=settings.APP_PORT, debug=True)
        except Exception as e:
            print(f"Ошибка запуска: {e}")
            raise
    except Exception as e:
        print(f"Ошибка: {e}")
        raise

