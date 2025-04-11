"""
Migration script to set a user as a super user.
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from greenbyte import db, createApp
from greenbyte.models import User

app = createApp()

def set_super_user(user_id):
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            print(f"User with ID {user_id} not found.")
            return
        
        user.access_level = 'admin'
        db.session.commit()
        print(f"User {user.firstName} {user.lastName} ({user.email}) is now a super user.")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python set_super_user.py <user_id>")
        sys.exit(1)
    
    try:
        user_id = int(sys.argv[1])
        set_super_user(user_id)
    except ValueError:
        print("User ID must be an integer.")
        sys.exit(1)
