from flask import Blueprint, flash, redirect, render_template, url_for, request
from flask_login import current_user
from app.services import BookService
from app.exceptions import DatabaseOperationError, DataAccessError, BookNotFoundError, BooksNotFoundError

books_bp = Blueprint('books', __name__)


@books_bp.route('/')
def home():
    try:
        top_books = BookService.get_top_books()
        top_books_by_genre = BookService.get_top_books_by_genre()
        return render_template(
            'books/home.html',
            top_books=top_books,
            top_books_by_genre=top_books_by_genre
        )

    except BooksNotFoundError:
        flash('Книги не найдены', 'error')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})

    except (DatabaseOperationError, DataAccessError):
        flash('Проблемы с базой данных', 'error')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})

    except Exception as e:
        print(f'Произошла ошибка: {e}')
        flash('Данные временно недоступны')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})


@books_bp.route('/catalog')
def catalog():
    try:
        books_by_genre = BookService.get_books_by_genre()
        if not books_by_genre:
            flash('Каталог пуст', 'error')
            return render_template('books/home.html', top_books=[], top_books_by_genre={})
        return render_template('books/catalog.html', books_by_genre=books_by_genre)
    except BooksNotFoundError:
        flash('Книги не найдены', 'error')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})
    except (DatabaseOperationError, DataAccessError):
        flash('Проблемы с базой данных', 'error')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})
    except Exception as e:
        print(f'Произошла ошибка: {e}')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})


@books_bp.route('/search', methods=['POST'])
def search():
    try:
        search_query = request.form.get('search_query')
        if not search_query or len(search_query.strip()) <= 2:
            flash('Слишком короткий запрос', 'error')
            return redirect(url_for('books.home'))
        result = BookService.search_book(search_query)
        return render_template('books/search-result.html', result=result, search_query=search_query)
    except BooksNotFoundError:
        flash('Книги не найдены', 'error')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})
    except Exception as e:
        print(f'Произошла ошибка: {e}')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})


@books_bp.route('/books/<book_id>', methods=['GET', 'POST'])
def book(book_id):
    try:
        book_by_id = BookService.get_book_by_id(book_id)
        reviews = BookService.get_reviews_by_book_id(book_id)
        book_quantity = BookService.check_book_quantity(book_id)

        if not book_by_id:
            flash('Книга не найдена', 'error')
            return render_template('books/home.html')

        form_type = request.form.get('form_type')

        if form_type == 'review' and current_user.is_authenticated:
            review_text = request.form['review_text'].strip()
            rating = int(request.form['rating'].strip())
            if review_text and rating:
                try:
                    BookService.add_review(review_text, current_user.id, book_id, rating)
                    flash('Отзыв успешно добавлен', 'success')
                except Exception as e:
                    print(f'Произошла ошибка: {e}')
                    flash('Ошибка добавления отзыва', 'error')

                return redirect(url_for('books.book', book_id=book_id))

        elif form_type == 'add_book':
            if current_user.is_authenticated:
                try:
                    BookService.update_cart(current_user.id, book_id)
                    flash('Книга добавлена в корзину', 'success')
                except Exception as e:
                    print(f'Произошла ошибка: {e}')
                    flash(f'Ошибка добавления книги в корзину', 'error')
                return redirect(url_for('books.book', book_id=book_id))
            else:
                flash('Для добавления книги в корзину необходимо авторизоваться', 'error')

        return render_template(
            'books/book.html',
            book=book_by_id, reviews=reviews,
            book_quantity=book_quantity
        )

    except BookNotFoundError:
        flash('Книга не найдена', 'error')
        return redirect(url_for('books.home'))

    except (DatabaseOperationError, DataAccessError):
        flash('Ошибка базы данных', 'error')
        return redirect(url_for('books.home'))

    except Exception as e:
        print(f'Ошибка: {e}')
        flash('Внутренняя ошибка сервера', 'error')
        return redirect(url_for('books.home'))



