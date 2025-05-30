from flask import Blueprint, flash, redirect, render_template, url_for, request, session
from flask_login import current_user, login_required
from app.cart.utils import CartService
from app.orders.utils import OrderService, DatabaseOperationError, DataAccessError, ServiceError
from app.orders.forms import CodeForm, CardDetailsForm
from random import randint


orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


@orders_bp.route('/new-order/<int:user_id>', methods=['GET', 'POST'])
@login_required
def new_order(user_id):
    try:
        if current_user.id != user_id:
            flash('У вас нет доступа к этой странице', 'error')
            return redirect(url_for('books.home'))

        try:
            available_items = CartService.get_available_items_from_cart(user_id)
        except Exception as e:
            print(f'Произошла ошибка: {e}')
            flash('Ошибка получения корзины', 'error')
            return redirect(url_for('cart.cart', user_id=user_id))

        if request.method == 'POST':
            form_type = request.form.get('form_type')

            if form_type == 'delivery_method':
                delivery_method = request.form.get('delivery_method')
                if delivery_method == 'door':
                    delivery_method = 'DOOR'
                elif delivery_method == 'pickup':
                    delivery_method = 'PICKUP'

                try:
                    store_addresses = OrderService.get_store_addresses()
                except Exception as e:
                    flash('Ошибка при получении адресов магазинов', 'error')
                    return redirect(url_for('orders.new_order', user_id=user_id))

                return render_template('orders/new-order.html',
                                       user_id=user_id,
                                       available_items=available_items,
                                       delivery_method=delivery_method.lower(),
                                       store_addresses=store_addresses)

            elif form_type == 'address_details':
                try:
                    delivery_method = 'DOOR'
                    city = request.form.get('city').strip()
                    street = request.form.get('street').strip()
                    house_number = request.form.get('house_number').strip()
                    building_number = request.form.get('building_number').strip()
                    entrance = request.form.get('entrance').strip()
                    intercom = request.form.get('intercom').strip()
                    floor = request.form.get('floor').strip()
                    apartment = request.form.get('apartment').strip()
                    comment = request.form.get('comment').strip()

                    address_parts = [
                        f'г. {city}',
                        f'ул. {street}',
                        f'д. {house_number}',
                        f'к. {building_number}' if building_number else None,
                        f'подъезд {entrance}' if entrance else None,
                        f'домофон {intercom}' if intercom else None,
                        f'этаж {floor}' if floor else None,
                        f'кв. {apartment}' if apartment else None,
                        f'комм. {comment}' if comment else None
                    ]

                    full_address = ', '.join(filter(None, address_parts)).lower()

                    OrderService.create_order(user_id, full_address, delivery_method)

                    last_order = OrderService.get_last_order(user_id)

                    for item in available_items:
                        OrderService.create_order_item(last_order['id'], item['book_id'], item['quantity'], item['price'], user_id)
                        OrderService.delete_cart_item(item['id'])

                    return redirect(url_for('orders.order_payment',
                                            user_id=user_id,
                                            order_id=last_order['id'],
                                            step='card_details'))

                except (DatabaseOperationError, DataAccessError, ServiceError) as e:
                    flash('Ошибка при создании заказа', 'error')
                    return redirect(url_for('orders.new_order', user_id=user_id))
                except ValueError as e:
                    flash(str(e), 'error')
                    return redirect(url_for('orders.new_order', user_id=user_id))

            elif form_type == 'store_address':
                try:
                    delivery_method = 'PICKUP'
                    full_address = request.form.get('store_address', '')
                    OrderService.create_order(user_id, full_address, delivery_method)
                    last_order = OrderService.get_last_order(user_id)

                    for item in available_items:
                        OrderService.create_order_item(last_order['id'], item['book_id'], item['quantity'], item['price'], user_id)
                        OrderService.delete_cart_item(item['id'])

                    return redirect(url_for('orders.order_payment', user_id=user_id, order_id=last_order['id'], step='card_details'))

                except (DatabaseOperationError, DataAccessError, ServiceError) as e:
                    flash('Ошибка при создании заказа', 'error')
                    return redirect(url_for('orders.new_order', user_id=user_id))
                except ValueError as e:
                    flash(str(e), 'error')
                    return redirect(url_for('orders.new_order', user_id=user_id))

        try:
            store_addresses = OrderService.get_store_addresses()
        except Exception as e:
            flash('Ошибка при получении адресов магазинов', 'error')
            store_addresses = []

        return render_template('orders/new-order.html',
                               user_id=user_id,
                               available_items=available_items,
                               store_addresses=store_addresses)

    except Exception as e:
        print(f'Неожиданная ошибка: {e}')
        flash('Внутренняя ошибка сервера', 'error')
        return redirect(url_for('books.home'))


@orders_bp.route('order_payment/<int:user_id>/<int:order_id>/<string:step>', methods=['GET', 'POST'])
@login_required
def order_payment(user_id, order_id, step):
    try:
        if current_user.id != user_id:
            flash('У вас нет доступа к этой странице', 'error')
            return redirect(url_for('books.home'))

        if step == 'card_details':
            form = CardDetailsForm()
        elif step == 'code':
            form = CodeForm()
        else:
            return redirect(url_for('orders.order_info', user_id=user_id, order_id=order_id))

        if form.validate_on_submit():
            if step == 'card_details':
                session['code'] = str(randint(1111, 9999))
                flash(f'Ваш код подтверждения оплаты: {session["code"]}', 'success')
                return redirect(url_for('orders.order_payment', user_id=user_id, order_id=order_id, step='code'))

            elif step == 'code' and session.get('code'):
                if form.code.data != session['code']:
                    flash(f'Неверный код, верный код: {session["code"]}', 'error')
                    return redirect(url_for('orders.order_payment', user_id=user_id, order_id=order_id, step='code'))
                session.pop('code', None)
                try:
                    OrderService.update_order_status(order_id, 'paid')
                    flash('Заказ оплачен!', 'success')
                    return redirect(url_for('orders.order_info',
                                            user_id=user_id,
                                            order_id=order_id))
                except (DatabaseOperationError, DataAccessError, ServiceError) as e:
                    flash('Ошибка при обновлении статуса заказа', 'error')
                    return redirect(url_for('orders.order_payment',
                                            user_id=user_id,
                                            order_id=order_id,
                                            step='code'))
                except ValueError as e:
                    flash(str(e), 'error')
                    return redirect(url_for('orders.order_payment',
                                            user_id=user_id,
                                            order_id=order_id,
                                            step='code'))
        try:
            order_items = OrderService.get_order_items_in_order(order_id)
            total_price = sum([order_item['price'] for order_item in order_items])
            return render_template('orders/order-payment.html',
                                   user_id=user_id,
                                   order_id=order_id,
                                   total_price=total_price,
                                   step=step,
                                   form=form)
        except (DatabaseOperationError, DataAccessError, ServiceError) as e:
            flash('Ошибка при получении информации о заказе', 'error')
            return redirect(url_for('books.home'))
        except Exception as e:
            print(f'Произошла ошибка: {e}')
            flash('Внутренняя ошибка сервера', 'error')
            return redirect(url_for('books.home'))

    except Exception as e:
        print(f'Произошла ошибка: {e}')
        flash('Внутренняя ошибка сервера', 'error')
        return redirect(url_for('books.home'))


@orders_bp.route('order-info/<int:user_id>/<int:order_id>')
@login_required
def order_info(user_id, order_id):
    try:
        if current_user.id != user_id:
            flash('У вас нет доступа к этой странице', 'error')
            return redirect(url_for('books.home'))

        try:
            order = OrderService.get_order_by_id(order_id)
            if not order:
                flash('Заказ не найден', 'error')
                return redirect(url_for('books.home'))

            order_items = OrderService.get_order_items_in_order(order_id)
            order['created_at'] = OrderService.time_to_string(order['created_at'])
            order['updated_at'] = OrderService.time_to_string(order['updated_at'])

            return render_template('orders/order-info.html',
                                   user_id=user_id,
                                   order_id=order_id,
                                   order=order,
                                   order_items=order_items)

        except (DatabaseOperationError, DataAccessError, ServiceError) as e:
            flash('Ошибка при получении информации о заказе', 'error')
            return redirect(url_for('books.home'))
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('books.home'))
        except Exception as e:
            print(f'Неожиданная ошибка: {e}')
            flash('Внутренняя ошибка сервера', 'error')
            return redirect(url_for('books.home'))

    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        flash('Внутренняя ошибка сервера', 'error')
        return redirect(url_for('books.home'))


@orders_bp.route('order-history/<int:user_id>')
@login_required
def order_history(user_id):
    try:
        if current_user.id != user_id:
            flash('У вас нет доступа к этой странице', 'error')
            return redirect(url_for('books.home'))

        try:
            users_orders = OrderService.users_orders_to_dict(user_id)
            for order in users_orders:
                order['created_at'] = OrderService.time_to_string(order['created_at'])
                order['updated_at'] = OrderService.time_to_string(order['updated_at'])

            return render_template('orders/order-history.html',
                                   user_id=user_id,
                                   users_orders=users_orders)

        except (DatabaseOperationError, DataAccessError, ServiceError) as e:
            flash('Ошибка при получении истории заказов', 'error')
            return redirect(url_for('books.home'))
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            flash('Внутренняя ошибка сервера', 'error')
            return redirect(url_for('books.home'))

    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        flash('Внутренняя ошибка сервера', 'error')
        return redirect(url_for('books.home'))

