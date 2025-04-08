"""
Migration script to add event_type_id column to calendar_event table
and create event_type table if it doesn't exist.
"""
from greenbyte import db, createApp
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

app = createApp()

def upgrade():
    with app.app_context():
        # Check if event_type table exists, if not create it
        if not db.engine.has_table('event_type'):
            print("Creating event_type table...")
            db.engine.execute('''
                CREATE TABLE event_type (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(50) NOT NULL,
                    color VARCHAR(20) NOT NULL,
                    user_id INTEGER NOT NULL,
                    is_default BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            ''')
            print("event_type table created successfully.")
        else:
            print("event_type table already exists.")

        # Check if event_type_id column exists in calendar_event table
        # If not, add it
        conn = db.engine.connect()
        result = conn.execute("PRAGMA table_info(calendar_event)")
        columns = [row[1] for row in result]
        
        if 'event_type_id' not in columns:
            print("Adding event_type_id column to calendar_event table...")
            db.engine.execute('''
                ALTER TABLE calendar_event
                ADD COLUMN event_type_id INTEGER,
                ADD FOREIGN KEY (event_type_id) REFERENCES event_type (id)
            ''')
            print("event_type_id column added successfully.")
        else:
            print("event_type_id column already exists.")

if __name__ == '__main__':
    upgrade()
