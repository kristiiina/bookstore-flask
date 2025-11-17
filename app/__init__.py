from flask import Flask
from app.config import settings
from app.database import engine, init_db, session_scope
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import LoginManager
from app.models import User

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'books.home'
login_manager.login_message = 'Необходимо авторизоваться для доступа к этой странице'


@login_manager.user_loader
def load_user(user_id):
    with session_scope() as db_session:
        # return db_session.query(User).get(int(user_id))
        user = db_session.query(User).get(int(user_id))
        if user:
            db_session.expunge(user)
        return user


from .auth.routes import auth_bp
from .books.routes import books_bp
from .cart.routes import cart_bp
from .orders.routes import orders_bp

app.register_blueprint(auth_bp)
app.register_blueprint(books_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(orders_bp)

app.db_session = scoped_session(sessionmaker(bind=engine))

