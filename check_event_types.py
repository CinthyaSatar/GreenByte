from greenbyte import createApp
from greenbyte.models import EventType, CalendarEvent

app = createApp()

with app.app_context():
    # Check event types
    print("Event Types:")
    for event_type in EventType.query.all():
        print(f"- {event_type.name} (Color: {event_type.color}, User: {event_type.user.username})")
    
    # Check calendar events
    print("\nCalendar Events with event_type_id:")
    events_with_type = CalendarEvent.query.filter(CalendarEvent.event_type_id.isnot(None)).all()
    if events_with_type:
        for event in events_with_type:
            print(f"- {event.title} (Type: {event.event_type.name if event.event_type else 'None'})")
    else:
        print("No events with event_type_id found yet.")
