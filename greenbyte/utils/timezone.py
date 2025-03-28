from datetime import datetime
from zoneinfo import ZoneInfo
from flask import current_app

def get_current_timezone():
    """Get the configured timezone"""
    return ZoneInfo(current_app.config['TIMEZONE'])

def localize_datetime(dt):
    """Convert a datetime to the configured timezone"""
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Assume UTC for naive datetimes
        dt = dt.replace(tzinfo=ZoneInfo('UTC'))
    
    return dt.astimezone(get_current_timezone())

def now_in_timezone():
    """Get current time in configured timezone"""
    return datetime.now(get_current_timezone())