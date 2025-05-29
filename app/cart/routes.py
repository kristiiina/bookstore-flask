from flask import Blueprint, flash, redirect, render_template, url_for, request
from flask_login import current_user, login_required
from app.cart.utils import CartService, DatabaseOperationError, DataAccessError, ServiceError


cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


@cart_bp.route('/<int:user_id>', methods=['GET', 'POST'])
@login_required
def cart(user_id):
    try:
        if current_user.id != user_id:
            return redirect(url_for('books.home'))

        try:
            users_cart = CartService.get_cart(user_id)
            available_items = CartService.get_available_items_from_cart(user_id)
            unavailable_items = CartService.get_unavailable_items_from_cart(user_id)
        except (DatabaseOperationError, DataAccessError, ServiceError) as e:
            print(f'Произошла ошибка: {e}')
            flash('Проблемы с базой данных', 'error')
            return redirect(url_for('cart.cart', user_id=user_id))

        if request.method == 'POST':
            form_type = request.form.get('form_type')

            if form_type == 'start_ordering':
                if not users_cart:
                    flash('Выберите хотя бы один товар для оформления заказа', 'error')
                    return redirect(url_for('cart.cart', user_id=user_id))
                if not available_items:
                    flash('В корзине отсутствуют доступные для заказа товары', 'error')
                    return redirect(url_for('cart.cart', user_id=user_id))
                return redirect(url_for('orders.new_order', user_id=user_id))

            if form_type == 'clear_cart':
                try:
                    CartService.clear_users_cart(user_id)
                    flash('Корзина очищена', 'success')
                except (DatabaseOperationError, DataAccessError, ServiceError) as e:
                    print(f'Произошла ошибка: {e}')
                    flash('Проблемы с базой данных', 'error')
                return redirect(url_for('cart.cart', user_id=user_id))

            item_id = request.form.get('cart_item_id', type=int)
            if item_id:
                try:
                    if form_type == 'delete_book':
                        CartService.handle_cart_actions(item_id, 'delete')
                        flash('Товар удалён', 'success')
                    elif form_type == 'add_book':
                        CartService.handle_cart_actions(item_id, 'add')
                        flash('Товар добавлен', 'success')
                except ValueError as e:
                    flash(str(e), 'error')
                except (DatabaseOperationError, DataAccessError, ServiceError):
                    flash('Ошибка при обновлении корзины', 'error')
            return redirect(url_for('cart.cart', user_id=user_id))

        return render_template('cart.html',
                               user_id=user_id,
                               users_cart=users_cart,
                               available_items=available_items,
                               unavailable_items=unavailable_items)
    except Exception as e:
        print(f'Произошла ошибка: {e}')
        flash('Данные временно недоступны')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})

