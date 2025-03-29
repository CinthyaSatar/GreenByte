import os
from zoneinfo import ZoneInfo

class Config():
    SECRET_KEY = "testing123"
    SECURITY_PASSWORD_SALT = 'random_secret_salt'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    TIMEZONE = 'America/Montreal'  # Montreal, Canada timezone
    MAIL_SERVER = 'smtp.gmail.com'  # Use your email provider's SMTP server
    MAIL_PORT = 587  # Use 465 for SSL or 587 for TLS
    MAIL_USE_TLS = True  # Use TLS for encryption
    MAIL_USE_SSL = False  # Make sure this is False if TLS is True
    MAIL_USERNAME = os.environ.get('EMAIL_USER')  # Your email
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')  # Your password rhrd neas irps ggvu
    MAIL_DEFAULT_SENDER = os.environ.get('EMAIL_USER')  # Default sender email
