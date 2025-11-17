from flask import Blueprint, flash, session, redirect, render_template, url_for
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user
from random import randint
from app.database import session_scope
from app.models import User
from app.auth.forms import (RegistrationForm,
                            LoginForm,
                            ResetPasswordPhoneForm,
                            ResetPasswordCodeForm,
                            ResetPasswordNewForm)
from app.exceptions import UserDoesNotExistError, DatabaseOperationError, DataAccessError
from app.services import AuthService


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    try:
        if form.validate_on_submit():
            AuthService.add_user(form.name.data, form.surname.data, form.email.data, form.phone.data, form.password.data)
            flash('Вы зарегистрированы!', 'success')
            return redirect(url_for('auth.login', form=form))

        return render_template('auth/register.html', form=form)

    except (DatabaseOperationError, DataAccessError):
        flash('Проблемы с базой данных', 'error')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})

    except Exception as e:
        print(f'Произошла ошибка: {e}')
        flash('Данные временно недоступны')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        form = LoginForm()
        if form.validate_on_submit():
            with session_scope() as db_session:
                user = db_session.query(User).filter_by(email=form.email.data).first()
                if not user:
                    flash('Пользователь не найден', 'error')
                    return redirect(url_for('auth.login'))

                if not check_password_hash(user.password_hash, form.password.data):
                    flash('Неверный пароль', 'error')
                    return redirect(url_for('auth.login'))

                login_user(user)
                return redirect(url_for('books.home'))

        return render_template('auth/login.html', form=form)

    except UserDoesNotExistError as e:
        print(f'Произошла ошибка: {e}')
        flash('Пользователя с таким e-mail не существует', 'error')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})

    except (DatabaseOperationError, DataAccessError) as e:
        print(f'Произошла ошибка: {e}')
        flash('Проблемы с базой данных', 'error')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})

    except Exception as e:
        print(f'Произошла ошибка: {e}')
        flash('Данные временно недоступны')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})


@auth_bp.route('/reset_password/<step>', methods=['GET', 'POST'])
def reset_password(step):
    try:
        if step not in ['phone', 'code', 'new_password']:
            return redirect(url_for('auth.reset_password', step='phone'))

        if step == 'phone':
            form = ResetPasswordPhoneForm()
        elif step == 'code':
            form = ResetPasswordCodeForm()
        elif step == 'new_password':
            form = ResetPasswordNewForm()
        else:
            return redirect(url_for('auth.reset_password', step='phone'))

        if form.validate_on_submit():
            if step == 'phone':
                with session_scope() as db_session:
                    user = db_session.query(User).filter_by(phone=form.phone.data).first()
                    if not user:
                        flash('Пользователя с таким номером телефона не существует', 'error')
                        return redirect(url_for('auth.reset_password', step='phone'))
                    session['user_id'] = user.id
                    session['code'] = str(randint(1111, 9999))
                    flash(f'Ваш код верификации: {session["code"]}', 'success')
                    return redirect(url_for('auth.reset_password', step='code'))

            elif step == 'code' and session.get('code'):
                if form.code.data != session['code']:
                    flash(f'Неверный код, ваш код: {session["code"]}', 'error')
                    return redirect(url_for('auth.reset_password', step='code'))
                session['new_password'] = True
                return redirect(url_for('auth.reset_password', step='new_password'))

            elif step == 'new_password' and session.get('new_password'):
                AuthService.update_password(session['user_id'], form.new_password.data)
                del session['user_id'], session['code'], session['new_password']
                flash('Пароль успешно изменен!', 'success')
                return redirect(url_for('auth.login'))

        return render_template('auth/reset-password.html', form=form, step=step)

    except (DatabaseOperationError, DataAccessError):
        flash('Проблемы с базой данных', 'error')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})

    except Exception as e:
        print(f'Произошла ошибка: {e}')
        flash('Данные временно недоступны')
        return render_template('books/home.html', top_books=[], top_books_by_genre={})


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('books.home'))

