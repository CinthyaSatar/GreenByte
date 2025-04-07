from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from greenbyte.config import Config
from datetime import datetime, timezone

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()  # Add this line

def timeago(date):
    """Convert a datetime to a 'time ago' string."""
    now = datetime.now(timezone.utc)
    # Make sure date is timezone-aware
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    diff = now - date

    seconds = diff.total_seconds()
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} min{"s" if minutes != 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 2592000:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f'{months} month{"s" if months != 1 else ""} ago'
    else:
        years = int(seconds / 31536000)
        return f'{years} year{"s" if years != 1 else ""} ago'

def createApp(configClass=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)  # Add this line

    # Register custom filters
    app.jinja_env.filters['timeago'] = timeago

    from greenbyte.users.routes import users
    from greenbyte.posts.routes import posts
    from greenbyte.main.routes import main
    from greenbyte.errors.handlers import errors
    from greenbyte.gardens.routes import gardens
    from greenbyte.commercial import commercial

    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(main)
    app.register_blueprint(errors)
    app.register_blueprint(gardens)
    app.register_blueprint(commercial)

    return app
