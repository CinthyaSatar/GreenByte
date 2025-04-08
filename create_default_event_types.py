from greenbyte import createApp, db
from greenbyte.models import EventType, User
from flask_login import current_user

app = createApp()

with app.app_context():
    # Get all users
    users = User.query.all()
    
    # Default event types with colors
    default_types = [
        {"name": "Birthday", "color": "#FF5733"},
        {"name": "Holiday", "color": "#33FF57"},
        {"name": "Meeting", "color": "#3357FF"},
        {"name": "Appointment", "color": "#FF33F5"},
        {"name": "Travel", "color": "#F5FF33"}
    ]
    
    # Create default event types for each user
    for user in users:
        print(f"Creating default event types for user: {user.username}")
        
        # Check if user already has event types
        existing_count = EventType.query.filter_by(user_id=user.id).count()
        if existing_count > 0:
            print(f"User {user.username} already has {existing_count} event types. Skipping.")
            continue
        
        # Create default event types
        for event_type in default_types:
            new_type = EventType(
                name=event_type["name"],
                color=event_type["color"],
                user_id=user.id,
                is_default=True
            )
            db.session.add(new_type)
        
        db.session.commit()
        print(f"Created {len(default_types)} default event types for user {user.username}")

print("Default event types created successfully!")
