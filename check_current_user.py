from greenbyte import createApp
from flask import session
from greenbyte.models import User

app = createApp()

with app.app_context():
    # Print all users
    users = User.query.all()
    print("All users:")
    for user in users:
        print(f"- ID: {user.id}, Username: {user.username}, Email: {user.email}")
