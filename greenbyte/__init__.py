from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager 
from flask_mail import Mail
from greenbyte.config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager= LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()



def createApp(configClass=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app) 
    bcrypt.init_app(app) 
    login_manager.init_app(app) 
    mail.init_app(app)  

    from greenbyte.users.routes import users 
    from greenbyte.posts.routes import posts 
    from greenbyte.main.routes import main 
    from greenbyte.errors.handlers import errors 

    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(main)
    app.register_blueprint(errors)

    return app