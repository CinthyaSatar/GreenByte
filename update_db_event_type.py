from greenbyte import createApp, db
from sqlalchemy import text

app = createApp()

with app.app_context():
    # Check if event_type table exists, if not create it
    with db.engine.connect() as conn:
        try:
            # Check if event_type table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='event_type'"))
            if not result.fetchone():
                print("Creating event_type table...")
                conn.execute(text('''
                    CREATE TABLE event_type (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(50) NOT NULL,
                        color VARCHAR(20) NOT NULL,
                        user_id INTEGER NOT NULL,
                        is_default BOOLEAN DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES user (id)
                    )
                '''))
                conn.commit()
                print("event_type table created successfully.")
            else:
                print("event_type table already exists.")
        except Exception as e:
            print(f"Error creating event_type table: {e}")
            conn.rollback()

    # Check if event_type_id column exists in calendar_event table
    with db.engine.connect() as conn:
        try:
            # Check if event_type_id column exists
            result = conn.execute(text("PRAGMA table_info(calendar_event)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'event_type_id' not in columns:
                print("Adding event_type_id column to calendar_event table...")
                conn.execute(text('ALTER TABLE calendar_event ADD COLUMN event_type_id INTEGER'))
                conn.commit()
                print("event_type_id column added successfully.")
            else:
                print("event_type_id column already exists.")
        except Exception as e:
            print(f"Error adding event_type_id column: {e}")
            conn.rollback()

print("Database update completed.")
