"""
Migration script to add access_level column to the user table.
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from greenbyte import db, createApp
from sqlalchemy import text

app = createApp()

def upgrade():
    with app.app_context():
        # Check if the access_level column already exists
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(user)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'access_level' not in columns:
                print("Adding access_level column to user table...")
                conn.execute(text("ALTER TABLE user ADD COLUMN access_level VARCHAR(20) NOT NULL DEFAULT 'user'"))
                conn.commit()
                print("access_level column added to user table.")
            else:
                print("access_level column already exists in user table.")

if __name__ == '__main__':
    upgrade()
