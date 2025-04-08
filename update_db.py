from greenbyte import createApp, db
from greenbyte.models import CalendarEvent
from sqlalchemy import text

app = createApp()

with app.app_context():
    # Add the zone_id column to the calendar_event table
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE calendar_event ADD COLUMN zone_id INTEGER REFERENCES zone(id)'))
        conn.commit()
    print("Added zone_id column to calendar_event table")
