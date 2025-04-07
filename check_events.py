from greenbyte import createApp
from greenbyte.models import CalendarEvent

app = createApp()

with app.app_context():
    print(f'Total events: {CalendarEvent.query.count()}')
    print('Recent events:')
    for event in CalendarEvent.query.order_by(CalendarEvent.created_at.desc()).limit(5).all():
        print(f'- {event.title} ({event.start_datetime})')
