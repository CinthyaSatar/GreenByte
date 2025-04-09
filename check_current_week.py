from greenbyte import createApp
from greenbyte.models import CalendarEvent, User
from datetime import datetime, timedelta
from flask_login import current_user

app = createApp()

with app.app_context():
    # Get the current date and calculate the start of the week (Monday)
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    print(f"Current week: {start_of_week.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')}")
    
    # Get all events
    all_events = CalendarEvent.query.all()
    print(f"Total events in database: {len(all_events)}")
    
    # Get events for the current week
    current_week_events = CalendarEvent.query.filter(
        CalendarEvent.start_datetime >= start_of_week,
        CalendarEvent.start_datetime <= end_of_week + timedelta(days=1)
    ).all()
    
    print(f"Events in current week: {len(current_week_events)}")
    
    # Print all events with their dates
    print("\nAll events:")
    for event in all_events:
        print(f"- {event.title}: {event.start_datetime.strftime('%Y-%m-%d')} (User ID: {event.user_id})")
