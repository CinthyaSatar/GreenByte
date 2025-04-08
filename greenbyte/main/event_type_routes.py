from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from greenbyte.models import EventType
from greenbyte import db

event_types = Blueprint('event_types', __name__)

@event_types.route("/event-types", methods=['GET'])
@login_required
def list_event_types():
    """Display a list of event types for the current user"""
    # Get all event types for the current user
    user_event_types = EventType.query.filter_by(user_id=current_user.id).all()
    
    return render_template('event_types/list.html', 
                          title='Event Types',
                          event_types=user_event_types)

@event_types.route("/event-types/new", methods=['GET', 'POST'])
@login_required
def new_event_type():
    """Create a new event type"""
    if request.method == 'POST':
        name = request.form.get('name')
        color = request.form.get('color')
        
        # Validate input
        if not name or not color:
            flash('Name and color are required', 'danger')
            return redirect(url_for('event_types.new_event_type'))
        
        # Create new event type
        event_type = EventType(
            name=name,
            color=color,
            user_id=current_user.id,
            is_default=False
        )
        
        db.session.add(event_type)
        db.session.commit()
        
        flash(f'Event type "{name}" created successfully!', 'success')
        return redirect(url_for('event_types.list_event_types'))
    
    return render_template('event_types/new.html', title='New Event Type')

@event_types.route("/event-types/<int:event_type_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_event_type(event_type_id):
    """Edit an existing event type"""
    event_type = EventType.query.get_or_404(event_type_id)
    
    # Ensure the user owns the event type
    if event_type.user_id != current_user.id:
        flash('You do not have permission to edit this event type', 'danger')
        return redirect(url_for('event_types.list_event_types'))
    
    # Prevent editing default event types
    if event_type.is_default:
        flash('Default event types cannot be edited', 'warning')
        return redirect(url_for('event_types.list_event_types'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        color = request.form.get('color')
        
        # Validate input
        if not name or not color:
            flash('Name and color are required', 'danger')
            return redirect(url_for('event_types.edit_event_type', event_type_id=event_type_id))
        
        # Update event type
        event_type.name = name
        event_type.color = color
        db.session.commit()
        
        flash(f'Event type "{name}" updated successfully!', 'success')
        return redirect(url_for('event_types.list_event_types'))
    
    return render_template('event_types/edit.html', 
                          title='Edit Event Type',
                          event_type=event_type)

@event_types.route("/event-types/<int:event_type_id>/delete", methods=['POST'])
@login_required
def delete_event_type(event_type_id):
    """Delete an event type"""
    event_type = EventType.query.get_or_404(event_type_id)
    
    # Ensure the user owns the event type
    if event_type.user_id != current_user.id:
        flash('You do not have permission to delete this event type', 'danger')
        return redirect(url_for('event_types.list_event_types'))
    
    # Prevent deleting default event types
    if event_type.is_default:
        flash('Default event types cannot be deleted', 'warning')
        return redirect(url_for('event_types.list_event_types'))
    
    # Delete the event type
    db.session.delete(event_type)
    db.session.commit()
    
    flash(f'Event type "{event_type.name}" deleted successfully!', 'success')
    return redirect(url_for('event_types.list_event_types'))

@event_types.route("/api/event-types", methods=['GET'])
@login_required
def get_event_types():
    """API endpoint to get all event types for the current user"""
    user_event_types = EventType.query.filter_by(user_id=current_user.id).all()
    return jsonify([event_type.to_dict() for event_type in user_event_types])
