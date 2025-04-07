from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from greenbyte.models import Post, CalendarEvent, CalendarEventInvitee, User, Garden, Plant, Zone

main = Blueprint('main', __name__)

@main.route("/")
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)

    for post in posts.items:
        # Format the read time
        post.formatted_date = post.date_posted.strftime('%B %d, %Y')
        post.formatted_read = f"{post.read_time} min read"

        # Get garden details
        if post.start_date:
            post.start_date_formatted = post.start_date.strftime('%B %Y')

    # Add default_style to the template context
    default_style = {
        'background': '#ffffff',
        'text': '#000000',
        'accent': '#4e73df'
    }

    return render_template('index.html',
                         posts=posts,
                         max=max,
                         min=min,
                         default_style=default_style)  # Add default_style here


@main.route("/calendar")
@login_required
def calendar():
    # Get the current date and calculate the start of the week (Monday)
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Format the date range for display
    date_range = f"{start_of_week.strftime('%B %d')} - {end_of_week.strftime('%d, %Y')}"

    # Get all events for the current user
    events = CalendarEvent.query.filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_datetime >= start_of_week,
        CalendarEvent.start_datetime <= end_of_week + timedelta(days=1)  # Add 1 day to include events on Sunday
    ).order_by(CalendarEvent.start_datetime).all()

    # Debug output
    print(f"Current user ID: {current_user.id}")
    print(f"Week range: {start_of_week.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')}")
    print(f"Found {len(events)} events for this week")
    for event in events:
        print(f"- {event.title}: {event.start_datetime.strftime('%Y-%m-%d %H:%M')} (weekday: {event.start_datetime.weekday()})")

    # Organize events by day of the week
    days_of_week = [
        {'name': 'Monday', 'date': start_of_week.strftime('%d'), 'events': []},
        {'name': 'Tuesday', 'date': (start_of_week + timedelta(days=1)).strftime('%d'), 'events': []},
        {'name': 'Wednesday', 'date': (start_of_week + timedelta(days=2)).strftime('%d'), 'events': []},
        {'name': 'Thursday', 'date': (start_of_week + timedelta(days=3)).strftime('%d'), 'events': []},
        {'name': 'Friday', 'date': (start_of_week + timedelta(days=4)).strftime('%d'), 'events': []},
        {'name': 'Saturday', 'date': (start_of_week + timedelta(days=5)).strftime('%d'), 'events': []},
        {'name': 'Sunday', 'date': end_of_week.strftime('%d'), 'events': []}
    ]

    # Add events to the appropriate day
    for event in events:
        weekday = event.start_datetime.weekday()  # 0 = Monday, 6 = Sunday
        if 0 <= weekday <= 6:  # Ensure the weekday is valid
            event_dict = {
                'id': event.id,
                'title': event.title,
                'time': event.start_datetime.strftime('%I:%M %p') if not event.all_day else 'All Day',
                'type': event.calendar_type,
                'all_day': event.all_day
            }
            days_of_week[weekday]['events'].append(event_dict)
            print(f"Added event '{event.title}' to {days_of_week[weekday]['name']} (index {weekday})")

    # Debug output for days_of_week
    for i, day in enumerate(days_of_week):
        print(f"{day['name']} ({day['date']}): {len(day['events'])} events")

    # Get upcoming events for the sidebar
    upcoming_events = CalendarEvent.query.filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_datetime >= today
    ).order_by(CalendarEvent.start_datetime).limit(5).all()

    # Get all gardens for the user to associate with events
    gardens = Garden.query.join(Garden.members).filter(User.id == current_user.id).all()

    # Get all plants for the user to associate with events
    plants = Plant.query.join(Zone, Plant.zone_id == Zone.id).join(Garden, Zone.garden_id == Garden.id).join(Garden.members).filter(User.id == current_user.id).all()

    return render_template('page_calendar.html',
                         title='Calendar',
                         days=days_of_week,
                         date_range=date_range,
                         upcoming_events=upcoming_events,
                         gardens=gardens,
                         plants=plants)

@main.route("/calendar/events", methods=['POST'])
@login_required
def add_event():
    # Get form data
    title = request.form.get('eventTitle')
    location = request.form.get('location')
    all_day = 'allDayEvent' in request.form
    start_date = request.form.get('startDate')
    start_time = request.form.get('startTime') if not all_day else '00:00'
    end_date = request.form.get('endDate')
    end_time = request.form.get('endTime') if not all_day else '23:59'
    repeat_type = request.form.get('repeatOption')
    repeat_end_date = request.form.get('endRepeat')
    calendar_type = request.form.get('calendar')
    invitees = request.form.get('invitees')
    alert_before_minutes = request.form.get('alert')
    is_private = 'privateEvent' in request.form
    url = request.form.get('eventUrl')
    description = request.form.get('notes')
    garden_id = request.form.get('garden_id')
    plant_id = request.form.get('plant_id')

    # Convert dates and times to datetime objects
    try:
        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M") if end_date else None
        repeat_end_datetime = datetime.strptime(repeat_end_date, "%Y-%m-%d") if repeat_end_date else None
    except ValueError as e:
        flash(f'Invalid date format: {str(e)}', 'danger')
        return redirect(url_for('main.calendar'))

    # Convert alert_before_minutes to integer if provided
    if alert_before_minutes:
        try:
            alert_before_minutes = int(alert_before_minutes)
        except ValueError:
            alert_before_minutes = None

    # Create new event
    event = CalendarEvent(
        title=title,
        description=description,
        location=location,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        all_day=all_day,
        repeat_type=repeat_type if repeat_type != 'none' else None,
        repeat_end_date=repeat_end_datetime,
        calendar_type=calendar_type,
        url=url,
        is_private=is_private,
        alert_before_minutes=alert_before_minutes,
        user_id=current_user.id,
        garden_id=garden_id if garden_id else None,
        plant_id=plant_id if plant_id else None
    )

    # Add event to database
    from greenbyte import db
    db.session.add(event)
    db.session.commit()

    # Process invitees if any
    if invitees:
        for invitee in invitees.split(','):
            invitee = invitee.strip()
            # Check if invitee is a user or an email
            user = User.query.filter_by(email=invitee).first()
            if user:
                event_invitee = CalendarEventInvitee(
                    event_id=event.id,
                    user_id=user.id,
                    status='pending'
                )
            else:
                # Assume it's an email
                event_invitee = CalendarEventInvitee(
                    event_id=event.id,
                    email=invitee,
                    status='pending'
                )
            db.session.add(event_invitee)
        db.session.commit()

    flash('Event added successfully!', 'success')
    return redirect(url_for('main.calendar'))

@main.route("/calendar/events/<int:event_id>", methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)

    # Ensure the user owns the event
    if event.user_id != current_user.id:
        flash('You do not have permission to access this event.', 'danger')
        return redirect(url_for('main.calendar'))

    if request.method == 'GET':
        return jsonify(event.to_dict())

    elif request.method == 'PUT':
        data = request.json

        # Update event fields
        event.title = data.get('title', event.title)
        event.description = data.get('description', event.description)
        event.location = data.get('location', event.location)

        # Handle datetime fields
        if 'start_datetime' in data:
            event.start_datetime = datetime.fromisoformat(data['start_datetime'])
        if 'end_datetime' in data and data['end_datetime']:
            event.end_datetime = datetime.fromisoformat(data['end_datetime'])
        else:
            event.end_datetime = None

        event.all_day = data.get('all_day', event.all_day)
        event.repeat_type = data.get('repeat_type', event.repeat_type)

        if 'repeat_end_date' in data and data['repeat_end_date']:
            event.repeat_end_date = datetime.fromisoformat(data['repeat_end_date'])
        else:
            event.repeat_end_date = None

        event.calendar_type = data.get('calendar_type', event.calendar_type)
        event.url = data.get('url', event.url)
        event.is_private = data.get('is_private', event.is_private)
        event.alert_before_minutes = data.get('alert_before_minutes', event.alert_before_minutes)
        event.garden_id = data.get('garden_id', event.garden_id)
        event.plant_id = data.get('plant_id', event.plant_id)

        # Update invitees if provided
        if 'invitees' in data:
            # Remove existing invitees
            CalendarEventInvitee.query.filter_by(event_id=event.id).delete()

            # Add new invitees
            for invitee in data['invitees']:
                if 'user_id' in invitee:
                    event_invitee = CalendarEventInvitee(
                        event_id=event.id,
                        user_id=invitee['user_id'],
                        status=invitee.get('status', 'pending')
                    )
                else:
                    event_invitee = CalendarEventInvitee(
                        event_id=event.id,
                        email=invitee['email'],
                        status=invitee.get('status', 'pending')
                    )
                db.session.add(event_invitee)

        from greenbyte import db
        db.session.commit()
        return jsonify({'message': 'Event updated successfully', 'event': event.to_dict()})

    elif request.method == 'DELETE':
        from greenbyte import db
        db.session.delete(event)
        db.session.commit()
        return jsonify({'message': 'Event deleted successfully'})

@main.route("/analytics")
def analytics():
    return render_template('analytics.html')

