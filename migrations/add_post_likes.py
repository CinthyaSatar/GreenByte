import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from greenbyte import db, createApp
from greenbyte.models import Post, User
from flask_sqlalchemy import SQLAlchemy

app = createApp()

# Create the post_like table
with app.app_context():
    # Check if the table already exists
    inspector = db.inspect(db.engine)
    if 'post_like' not in inspector.get_table_names():
        # Create the post_like table
        from sqlalchemy import text
        sql = text('''
        CREATE TABLE post_like (
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, post_id),
            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES post (id) ON DELETE CASCADE
        )
        ''')
        db.session.execute(sql)
        db.session.commit()
        print("Created post_like table")
    else:
        print("post_like table already exists")
