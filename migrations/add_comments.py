"""
Migration script to add comments table to the database.
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from greenbyte import db, createApp
from sqlalchemy import text

app = createApp()

# Create the comments table
with app.app_context():
    # Check if the table already exists
    inspector = db.inspect(db.engine)
    if 'comment' not in inspector.get_table_names():
        # Create the comment table
        sql = text('''
        CREATE TABLE comment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            parent_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES post (id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES comment (id) ON DELETE CASCADE
        )
        ''')
        db.session.execute(sql)
        db.session.commit()
        print("Created comment table")
    else:
        print("comment table already exists")
