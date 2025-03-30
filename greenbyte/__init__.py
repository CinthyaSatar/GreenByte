from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from greenbyte.config import Config

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()  # Add this line

def createApp(configClass=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app) 
    migrate.init_app(app, db)
    bcrypt.init_app(app) 
    login_manager.init_app(app) 
    mail.init_app(app)
    csrf.init_app(app)  # Add this line

    from greenbyte.users.routes import users 
    from greenbyte.posts.routes import posts 
    from greenbyte.main.routes import main 
    from greenbyte.errors.handlers import errors 
    from greenbyte.gardens.routes import gardens 

    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(main)
    app.register_blueprint(errors)
    app.register_blueprint(gardens)

    return app
