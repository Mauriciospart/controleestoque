from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
import os

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'main.login'
mail = Mail()
migrate = Migrate()

def create_app():
    # Use the application factory pattern
    app = Flask(__name__, instance_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance'))

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # already exists

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'), # Provide a default for dev
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'site.db')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER='uploads',
        MAIL_SERVER=os.environ.get('MAIL_SERVER', 'smtp.googlemail.com'),
        MAIL_PORT=int(os.environ.get('MAIL_PORT', '587')),
        MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1'],
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', 'your-email@gmail.com'),
        LOW_STOCK_EMAIL=os.environ.get('LOW_STOCK_EMAIL')
    )

    db.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from .routes import main as main_blueprint
        app.register_blueprint(main_blueprint)

        from . import models

        @login.user_loader
        def load_user(id):
            return models.User.query.get(int(id))

        return app
