from greenbyte import createApp, db
from greenbyte.models import CalendarEvent
from sqlalchemy import text

app = createApp()

with app.app_context():
    # Add the completed and completed_at columns to the calendar_event table
    with db.engine.connect() as conn:
        try:
            conn.execute(text('ALTER TABLE calendar_event ADD COLUMN completed BOOLEAN DEFAULT FALSE'))
            conn.commit()
            print("Added completed column to calendar_event table")
        except Exception as e:
            print(f"Error adding completed column: {e}")
            conn.rollback()

        try:
            conn.execute(text('ALTER TABLE calendar_event ADD COLUMN completed_at DATETIME'))
            conn.commit()
            print("Added completed_at column to calendar_event table")
        except Exception as e:
            print(f"Error adding completed_at column: {e}")
            conn.rollback()
