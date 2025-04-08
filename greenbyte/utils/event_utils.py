from datetime import datetime
from greenbyte.models import CalendarEvent
from greenbyte.utils.timezone import now_in_timezone, localize_datetime

def update_event_completion_status(event):
    """
    Update the completion status of an event based on its type and date.

    For regular events (non-TODO), mark as completed when their end date has passed.
    For TODO events, only mark as completed when explicitly checked by a user.

    Args:
        event (CalendarEvent): The event to update

    Returns:
        bool: True if the event status was changed, False otherwise
    """
    current_time = now_in_timezone()
    status_changed = False

    # Skip if already completed
    if event.completed:
        return False

    # For non-TODO events, mark as completed when their end date has passed
    if event.calendar_type.lower() != 'todo':
        end_time = event.end_datetime or event.start_datetime
        # Make sure both datetimes are timezone-aware for comparison
        if end_time:
            # Localize the datetime if it's naive
            if end_time.tzinfo is None:
                end_time = localize_datetime(end_time)

            if end_time < current_time:
                event.completed = True
                event.completed_at = current_time
                status_changed = True

    return status_changed

def is_event_overdue(event):
    """
    Check if a TODO event is overdue (past its scheduled date but not completed).

    Args:
        event (CalendarEvent): The event to check

    Returns:
        bool: True if the event is overdue, False otherwise
    """
    if event.calendar_type.lower() != 'todo':
        return False

    current_time = now_in_timezone()
    end_time = event.end_datetime or event.start_datetime

    # Make sure both datetimes are timezone-aware for comparison
    if end_time and end_time.tzinfo is None:
        end_time = localize_datetime(end_time)

    return not event.completed and end_time and end_time < current_time

def batch_update_events_completion(events):
    """
    Update completion status for a batch of events.

    Args:
        events (list): List of CalendarEvent objects

    Returns:
        int: Number of events updated
    """
    from greenbyte import db

    updated_count = 0
    for event in events:
        if update_event_completion_status(event):
            updated_count += 1

    if updated_count > 0:
        db.session.commit()

    return updated_count
