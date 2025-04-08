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
@main.route("/calendar/<date_str>")
@login_required
def calendar(date_str=None):
    # If a date is provided, use it as the reference date, otherwise use today
    if date_str:
        try:
            reference_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            # If invalid date format, default to today
            reference_date = datetime.now()
    else:
        reference_date = datetime.now()

    # Calculate the start of the week (Monday) based on the reference date
    start_of_week = reference_date - timedelta(days=reference_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Calculate previous and next week dates
    prev_week = (start_of_week - timedelta(days=7)).strftime('%Y-%m-%d')
    next_week = (start_of_week + timedelta(days=7)).strftime('%Y-%m-%d')

    # Calculate month calendar data
    month_start = reference_date.replace(day=1)
    month_name = month_start.strftime('%B')
    year = month_start.strftime('%Y')

    # Calculate previous and next month dates
    prev_month = (month_start - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d')
    next_month_date = month_start.replace(day=28) + timedelta(days=4)  # This will always be in the next month
    next_month = next_month_date.replace(day=1).strftime('%Y-%m-%d')

    # Get the first day of the month and the number of days in the month
    first_day_weekday = month_start.weekday()  # 0 = Monday, 6 = Sunday

    # Get the number of days in the month
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    days_in_month = (next_month_start - month_start).days

    # Get all events for the month (including a few days before and after)
    month_start_date = month_start - timedelta(days=10)  # Include some days from previous month
    month_end_date = next_month_start + timedelta(days=10)  # Include some days from next month

    # Get all events in the date range
    month_events = CalendarEvent.query.filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_datetime >= month_start_date,
        CalendarEvent.start_datetime <= month_end_date
    ).all()

    # Create a set of dates that have events for quick lookup
    event_dates = set()
    for event in month_events:
        event_date = event.start_datetime.strftime('%Y-%m-%d')
        event_dates.add(event_date)

    # Get the previous month's days that appear in the first week of the current month
    prev_month_days = []
    if first_day_weekday > 0:  # If the month doesn't start on Monday
        prev_month_end = month_start - timedelta(days=1)
        for i in range(first_day_weekday):
            day = prev_month_end - timedelta(days=i)
            day_str = day.strftime('%Y-%m-%d')
            prev_month_days.insert(0, {
                'day': day.day,
                'date': day_str,
                'date_str': day_str,
                'current_month': False,
                'has_events': day_str in event_dates
            })

    # Get the current month's days
    current_month_days = []
    for i in range(1, days_in_month + 1):
        day = month_start.replace(day=i)
        day_str = day.strftime('%Y-%m-%d')
        current_month_days.append({
            'day': day.day,
            'date': day_str,
            'date_str': day_str,
            'current_month': True,
            'has_events': day_str in event_dates
        })

    # Get the next month's days that appear in the last week of the current month
    next_month_days = []
    total_days = len(prev_month_days) + len(current_month_days)

    # Calculate how many days we need to complete the calendar
    # First, determine if we need 5 or 6 weeks
    days_in_5_weeks = 35  # 5 weeks * 7 days
    days_in_6_weeks = 42  # 6 weeks * 7 days

    # If the total days from previous and current month fit in 5 weeks (35 days),
    # or if the 6th week would be entirely in the next month, use 5 weeks
    if total_days <= days_in_5_weeks or (total_days > days_in_5_weeks and total_days % 7 == 0):
        remaining_days = days_in_5_weeks - total_days
    else:
        remaining_days = days_in_6_weeks - total_days

    if remaining_days > 0:
        next_month_start = month_start.replace(day=1)
        if next_month_start.month == 12:
            next_month_start = next_month_start.replace(year=next_month_start.year + 1, month=1)
        else:
            next_month_start = next_month_start.replace(month=next_month_start.month + 1)

        for i in range(1, remaining_days + 1):
            day = next_month_start.replace(day=i)
            day_str = day.strftime('%Y-%m-%d')
            next_month_days.append({
                'day': day.day,
                'date': day_str,
                'date_str': day_str,
                'current_month': False,
                'has_events': day_str in event_dates
            })

    # Combine all days and split into weeks
    all_days = prev_month_days + current_month_days + next_month_days
    month_calendar = [all_days[i:i+7] for i in range(0, len(all_days), 7)]

    # Get the current day for highlighting in the calendar
    current_day = datetime.now().strftime('%Y-%m-%d')

    # Format the date range for display
    date_range = f"{start_of_week.strftime('%B %d')} - {end_of_week.strftime('%d, %Y')}"

    # Get all events for the current user for this specific week
    # Use strict date range to ensure events are only shown in their correct week
    week_start_datetime = datetime.combine(start_of_week, datetime.min.time())
    week_end_datetime = datetime.combine(end_of_week, datetime.max.time())

    events = CalendarEvent.query.filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_datetime >= week_start_datetime,
        CalendarEvent.start_datetime <= week_end_datetime
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

    # Add events to the appropriate day(s)
    for event in events:
        # Get the event start date and ensure it's within our week
        event_start_date = event.start_datetime.date()
        days_since_start = (event_start_date - start_of_week.date()).days

        # Calculate event duration
        if event.end_datetime:
            event_end_date = event.end_datetime.date()
            event_duration = (event_end_date - event_start_date).days + 1  # +1 to include the end day
        else:
            event_end_date = event_start_date
            event_duration = 1

        # Determine if this is a multi-day event
        is_multi_day = event_duration > 1

        # If the event starts before this week, adjust the start day
        if days_since_start < 0:
            # Calculate how many days of the event have already passed
            days_passed = abs(days_since_start)
            # Adjust the start day to the beginning of the week
            days_since_start = 0
            # Adjust the duration to account for days that have passed
            event_duration -= days_passed

        # If the event ends after this week, adjust the end day
        if days_since_start + event_duration > 7:
            event_duration = 7 - days_since_start

        # Only process events that have at least one day in this week
        if event_duration > 0 and 0 <= days_since_start <= 6:
            # For multi-day events, create an event for each day
            for day_offset in range(event_duration):
                current_day = days_since_start + day_offset
                if current_day > 6:  # Skip days beyond Sunday
                    break

                # Calculate which day of the event this is (1-based)
                if days_since_start < 0:
                    day_number = day_offset + abs(days_since_start) + 1
                else:
                    day_number = day_offset + 1

                # Create the event dictionary for this day
                event_dict = {
                    'id': event.id,
                    'title': event.title,
                    'time': event.start_datetime.strftime('%I:%M %p') if not event.all_day else 'All Day',
                    'type': event.calendar_type,
                    'all_day': event.all_day,
                    'multi_day': is_multi_day,
                    'duration': event_duration,
                    'day_number': day_number,
                    'total_days': event_duration if not is_multi_day else (event_end_date - event_start_date).days + 1
                }

                # Add the event to the appropriate day
                days_of_week[current_day]['events'].append(event_dict)
                print(f"Added event '{event.title}' to {days_of_week[current_day]['name']} (index {current_day}) - Date: {(start_of_week + timedelta(days=current_day)).strftime('%Y-%m-%d')}")

    # Debug output for days_of_week
    for i, day in enumerate(days_of_week):
        print(f"{day['name']} ({day['date']}): {len(day['events'])} events")

    # Get upcoming events for the sidebar
    upcoming_events = CalendarEvent.query.filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_datetime >= datetime.now()
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
                         plants=plants,
                         prev_week=prev_week,
                         next_week=next_week,
                         month_calendar=month_calendar,
                         month_name=month_name,
                         year=year,
                         prev_month=prev_month,
                         next_month=next_month,
                         current_day=current_day)

@main.route("/calendar/add", methods=['GET'])
@login_required
def add_calendar_event():
    # Get all gardens for the user to associate with events
    gardens = Garden.query.join(Garden.members).filter(User.id == current_user.id).all()

    # Get all plants for the user to associate with events
    plants = Plant.query.join(Zone, Plant.zone_id == Zone.id).join(Garden, Zone.garden_id == Garden.id).join(Garden.members).filter(User.id == current_user.id).all()

    return render_template('add_calendar_event.html',
                         title='Add Event',
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
    print(f"Calendar type from form: {calendar_type}")

    # Force calendar_type to 'todo' if it's coming from the TODO task form
    if calendar_type == 'todo':
        print("Setting calendar_type to 'todo'")
    invitees = request.form.get('invitees')
    alert_before_minutes = request.form.get('alert')
    is_private = 'privateEvent' in request.form
    url = request.form.get('eventUrl')
    description = request.form.get('notes')
    garden_id = request.form.get('garden_id')
    zone_id = request.form.get('zone_id')
    plant_id = request.form.get('plant_id')

    # Server-side validation
    errors = []

    # Validate required fields
    if not title:
        errors.append('Event title is required')
    if not start_date:
        errors.append('Start date is required')
    if not end_date:
        errors.append('End date is required')
    if not all_day and not start_time:
        errors.append('Start time is required for non-all-day events')
    if not all_day and not end_time:
        errors.append('End time is required for non-all-day events')
    if repeat_type == 'on' and not repeat_end_date:
        errors.append('End repeat date is required when repeat is enabled')

    # If there are validation errors, flash them and redirect back
    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('main.calendar'))

    # Convert dates and times to datetime objects
    try:
        # Add validation to ensure start_time and end_time are properly formatted
        if not all_day:
            if not start_time or len(start_time.strip()) < 5:
                flash('Invalid start time format. Please use HH:MM format.', 'danger')
                return redirect(url_for('main.calendar'))
            if not end_time or len(end_time.strip()) < 5:
                flash('Invalid end time format. Please use HH:MM format.', 'danger')
                return redirect(url_for('main.calendar'))

        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M") if end_date else None
        repeat_end_datetime = datetime.strptime(repeat_end_date, "%Y-%m-%d") if repeat_end_date else None

        # Validate that end date is not before start date
        if end_datetime and end_datetime < start_datetime:
            flash('End date/time cannot be before start date/time', 'danger')
            return redirect(url_for('main.calendar'))

    except ValueError as e:
        flash(f'Invalid date or time format: {str(e)}', 'danger')
        return redirect(url_for('main.calendar'))

    # Convert alert_before_minutes to integer if provided
    if alert_before_minutes:
        try:
            alert_before_minutes = int(alert_before_minutes)
        except ValueError:
            alert_before_minutes = None

    # Create new event
    print(f"Creating event with calendar_type: {calendar_type}")
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
        zone_id=zone_id if zone_id else None,
        plant_id=plant_id if plant_id else None
    )

    # Ensure the calendar_type is set correctly
    if calendar_type == 'todo':
        event.calendar_type = 'todo'

    # Add event to database
    from greenbyte import db
    db.session.add(event)
    db.session.commit()

    # Debug: Print the saved event details
    print(f"Saved event: ID={event.id}, Title={event.title}, Calendar Type={event.calendar_type}")

    # Double-check the calendar_type after saving
    saved_event = CalendarEvent.query.get(event.id)
    print(f"Double-check: Calendar Type after save={saved_event.calendar_type}")

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

@main.route("/api/gardens/<int:garden_id>/zones", methods=['GET'])
@login_required
def get_garden_zones(garden_id):
    # Verify the user has access to this garden
    garden = Garden.query.get_or_404(garden_id)
    if current_user not in garden.members:
        return jsonify({'error': 'Access denied'}), 403

    # Get all zones for the garden
    zones = Zone.query.filter_by(garden_id=garden_id).all()

    # Convert to JSON
    zones_data = [{'id': zone.id, 'name': zone.name} for zone in zones]

    return jsonify(zones_data)

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

@main.route("/calendar/events/<int:event_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)

    # Ensure the user owns the event
    if event.user_id != current_user.id:
        flash('You do not have permission to edit this event.', 'danger')
        return redirect(url_for('main.calendar'))

    # Get all gardens for the user to associate with events
    gardens = Garden.query.join(Garden.members).filter(User.id == current_user.id).all()

    # Get all plants for the user to associate with events
    plants = Plant.query.join(Zone, Plant.zone_id == Zone.id).join(Garden, Zone.garden_id == Garden.id).join(Garden.members).filter(User.id == current_user.id).all()

    if request.method == 'POST':
        # Get form data
        title = request.form.get('eventTitle')
        location = request.form.get('location')
        all_day = 'allDayEvent' in request.form
        start_date = request.form.get('startDate')
        start_time = request.form.get('startTime') if not all_day else '00:00'
        end_date = request.form.get('endDate')
        end_time = request.form.get('endTime') if not all_day else '23:59'
        repeat_type = request.form.get('repeatOption')
        repeat_end_date = request.form.get('endRepeatDate') if request.form.get('endRepeat') == 'on' else None
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
            return redirect(url_for('main.edit_event', event_id=event_id))

        # Convert alert_before_minutes to integer if provided
        if alert_before_minutes:
            try:
                alert_before_minutes = int(alert_before_minutes)
            except ValueError:
                alert_before_minutes = None

        # Update event fields
        event.title = title
        event.description = description
        event.location = location
        event.start_datetime = start_datetime
        event.end_datetime = end_datetime
        event.all_day = all_day
        event.repeat_type = repeat_type if repeat_type != 'none' else None
        event.repeat_end_date = repeat_end_datetime
        event.calendar_type = calendar_type
        print(f"Setting calendar_type to {calendar_type} in edit_event")

        # Ensure the calendar_type is set correctly
        if calendar_type == 'todo':
            event.calendar_type = 'todo'
            print("Forcing calendar_type to 'todo' in edit_event")

        event.url = url
        event.is_private = is_private
        event.alert_before_minutes = alert_before_minutes
        event.garden_id = garden_id if garden_id else None
        event.plant_id = plant_id if plant_id else None

        # Process invitees if any
        if invitees:
            # Remove existing invitees
            CalendarEventInvitee.query.filter_by(event_id=event.id).delete()

            for invitee in invitees.split(','):
                invitee = invitee.strip()
                if not invitee:
                    continue

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
                from greenbyte import db
                db.session.add(event_invitee)

        from greenbyte import db
        db.session.commit()

        # Double-check the calendar_type after saving
        saved_event = CalendarEvent.query.get(event.id)
        print(f"Double-check: Calendar Type after edit={saved_event.calendar_type}")

        flash('Event updated successfully!', 'success')
        return redirect(url_for('main.calendar'))

    return render_template('edit_calendar_event.html',
                         title='Edit Event',
                         event=event,
                         gardens=gardens,
                         plants=plants)

@main.route("/calendar/events/<int:event_id>/delete", methods=['POST'])
@login_required
def delete_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)

    # Ensure the user owns the event
    if event.user_id != current_user.id:
        flash('You do not have permission to delete this event.', 'danger')
        return redirect(url_for('main.calendar'))

    from greenbyte import db
    db.session.delete(event)
    db.session.commit()

    flash('Event deleted successfully!', 'success')
    return redirect(url_for('main.calendar'))

@main.route("/analytics")
def analytics():
    return render_template('analytics.html')

