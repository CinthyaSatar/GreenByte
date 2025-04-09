
from flask import Blueprint, render_template, flash, redirect, url_for, abort, request, jsonify
from flask_login import current_user, login_required
from greenbyte import db
from greenbyte.gardens.forms import GardenForm, ZoneForm, PlantForm
from greenbyte.models import (
    User, Garden, Zone, Plant, PlantTracking,
    Harvest, user_garden, PlantDetail, PlantVariety, CalendarEvent
)
from datetime import datetime, timedelta, date
from flask import current_app
from greenbyte.utils.timezone import now_in_timezone, localize_datetime

gardens = Blueprint('gardens', __name__)

@gardens.route("/garden/new", methods=['GET', 'POST'])
@login_required
def add_garden():
    form = GardenForm()
    if form.validate_on_submit():
        garden = Garden(
            name=form.name.data,
            location=form.location.data,
            owner_id=current_user.id
        )
        # Add current user as a member
        garden.members.append(current_user)

        # Process selected members from the form
        selected_members_json = request.form.get('selected_members', '[]')
        try:
            import json
            selected_member_ids = json.loads(selected_members_json)

            # Add selected members to the garden
            if selected_member_ids and isinstance(selected_member_ids, list):
                for member_id in selected_member_ids:
                    # Skip if it's the current user (already added)
                    if member_id != current_user.id:
                        user = User.query.get(member_id)
                        if user:
                            garden.members.append(user)
        except Exception as e:
            print(f"Error processing members: {e}")
            # Continue with garden creation even if member processing fails

        db.session.add(garden)
        db.session.commit()

        flash('Your garden has been created!', 'success')
        return redirect(url_for('gardens.view_gardens'))

    return render_template('add_page_gardens.html',
                         title='New Garden',
                         form=form)


@gardens.route("/gardens")
@login_required
def view_gardens():
    gardens = Garden.query.join(user_garden).filter(
        user_garden.c.user_id == current_user.id
    ).order_by(Garden.last_updated.desc()).all()

    # Add status style mapping
    status_style_mapping = {
        'Seedling': {
            'bg': 'bg-info',
            'icon': 'seedling',
            'extra_style': ''
        },
        'Growing': {
            'bg': 'bg-primary',
            'icon': 'leaf',
            'extra_style': ''
        },
        'Mature': {
            'bg': 'bg-success',
            'icon': 'tree',
            'extra_style': ''
        },
        'Harvesting': {
            'bg': 'bg-warning',
            'icon': 'harvest',
            'extra_style': ''
        }
    }

    # Add default style
    default_style = {
        'bg': 'bg-secondary',
        'icon': 'circle',
        'extra_style': ''
    }

    # Get upcoming events for the next 7 days
    today = date.today()
    next_week = today + timedelta(days=7)

    # Import event utilities
    from greenbyte.utils.event_utils import batch_update_events_completion, is_event_overdue

    # Get all events for the current user
    user_events = CalendarEvent.query.filter_by(user_id=current_user.id).all()

    # Update completion status for events
    updated_count = batch_update_events_completion(user_events)

    # Fetch all upcoming events for the user's gardens, zones, and plants
    # Also include TODO tasks regardless of their associations
    upcoming_events = CalendarEvent.query.filter(
        CalendarEvent.user_id == current_user.id,
        ((CalendarEvent.start_datetime >= today) |
         ((CalendarEvent.calendar_type == 'todo') & (CalendarEvent.completed == False))),  # Include overdue TODO tasks
        CalendarEvent.start_datetime <= next_week,
        ((CalendarEvent.garden_id != None) | (CalendarEvent.zone_id != None) | (CalendarEvent.plant_id != None) | (CalendarEvent.calendar_type == 'todo'))
    ).order_by(CalendarEvent.start_datetime).all()

    # Create dictionaries to organize events by garden, zone, and plant
    garden_events = {}
    zone_events = {}
    plant_events = {}
    todo_events_list = []

    for event in upcoming_events:
        # Add TODO events to a separate list if they don't have garden, zone, or plant associations
        # Only include non-completed TODO tasks
        if event.calendar_type == 'todo' and not event.completed and not (event.garden_id or event.zone_id or event.plant_id):
            todo_events_list.append(event)

        # Add to garden events
        if event.garden_id:
            if event.garden_id not in garden_events:
                garden_events[event.garden_id] = []
            garden_events[event.garden_id].append(event)

        # Add to zone events
        if event.zone_id:
            if event.zone_id not in zone_events:
                zone_events[event.zone_id] = []
            zone_events[event.zone_id].append(event)

        # Add to plant events
        if event.plant_id:
            if event.plant_id not in plant_events:
                plant_events[event.plant_id] = []
            plant_events[event.plant_id].append(event)

    # Get current time for checking overdue tasks
    now = now_in_timezone()

    return render_template('page_gardens.html',
                         gardens=gardens,
                         status_style_mapping=status_style_mapping,
                         default_style=default_style,
                         garden_events=garden_events,
                         zone_events=zone_events,
                         plant_events=plant_events,
                         todo_events_list=todo_events_list,
                         now=now,
                         all_events=upcoming_events)


@gardens.route('/garden/<int:garden_id>/add_zone', methods=['GET', 'POST'])
@login_required
def add_zone(garden_id):
    garden = Garden.query.get_or_404(garden_id)

    # Check if user is a member of the garden
    if current_user not in garden.members:
        abort(403)

    form = ZoneForm()
    if form.validate_on_submit():
        # Create a new zone
        zone = Zone(
            name=form.name.data,
            garden_id=garden_id
        )
        db.session.add(zone)
        db.session.commit()

        # Get statuses from form
        statuses = []
        for status_field in form.plant_statuses:
            if status_field.data and status_field.data.strip():
                statuses.append(status_field.data.strip())

        # Remove duplicates while preserving order
        statuses = list(dict.fromkeys(statuses))

        if statuses:
            try:
                zone.set_plant_statuses(statuses)
                db.session.commit()
                flash('Zone added successfully!', 'success')
                return redirect(url_for('gardens.view_gardens'))
            except Exception as e:
                db.session.rollback()
                flash('Error setting zone statuses.', 'danger')
        else:
            flash('At least one plant status is required.', 'danger')

    return render_template('add_zone.html', form=form, garden=garden)


@gardens.route("/plant/<int:plant_id>/move/<int:zone_id>")
@login_required
def move_plant(plant_id, zone_id):
    plant = Plant.query.get_or_404(plant_id)
    new_zone = Zone.query.get_or_404(zone_id)

    # Verify user has permission for both current and new zones
    current_garden = Garden.query.join(Zone).join(Plant).filter(Plant.id == plant_id).first()
    new_garden = Garden.query.join(Zone).filter(Zone.id == zone_id).first()

    if not (current_user in current_garden.members and current_user in new_garden.members):
        abort(403)

    # Check if the plant is already in the target zone
    old_zone = plant.zone.name
    if plant.zone_id == zone_id:
        flash(f'{plant.plant_detail.name} is already in {new_zone.name}!', 'info')
        return redirect(url_for('gardens.view_gardens'))

    # Check if the plant's current status is available in the target zone
    current_status = plant.status
    target_zone_statuses = new_zone.get_plant_statuses()
    if current_status not in target_zone_statuses:
        flash(f"Cannot move {plant.plant_detail.name} to {new_zone.name}. The plant's current status '{current_status}' is not available in the target zone.", 'danger')
        return redirect(url_for('gardens.view_gardens'))

    # Move the plant
    plant.zone_id = zone_id

    # Update the timestamp with correct timezone
    current_garden.last_updated = now_in_timezone()
    new_garden.last_updated = now_in_timezone()

    db.session.commit()

    flash(f'Moved {plant.plant_detail.name} from {old_zone} to {new_zone.name}!', 'success')
    return redirect(url_for('gardens.view_gardens'))


@gardens.route("/api/plant/<int:plant_id>/move/<int:zone_id>", methods=['POST'])
@login_required
def move_plant_ajax(plant_id, zone_id):
    try:
        plant = Plant.query.get_or_404(plant_id)
        new_zone = Zone.query.get_or_404(zone_id)

        # Verify user has permission for both current and new zones
        current_garden = Garden.query.join(Zone).join(Plant).filter(Plant.id == plant_id).first()
        new_garden = Garden.query.join(Zone).filter(Zone.id == zone_id).first()

        if not (current_user in current_garden.members and current_user in new_garden.members):
            return jsonify({'success': False, 'error': 'Permission denied'}), 403

        # Get plant details before moving
        plant_name = plant.plant_detail.name
        old_zone_name = plant.zone.name
        old_zone_id = plant.zone_id

        # Check if the plant is already in the target zone
        if old_zone_id == zone_id:
            print(f"Plant {plant_id} is already in zone {zone_id}")
            # Get all zones in the garden for move dropdown
            garden_zones = [z for z in new_zone.garden.zones]
            return jsonify({
                'success': True,
                'message': f'{plant_name} is already in {new_zone.name}',
                'plant_id': plant_id,
                'plant_name': plant_name,
                'new_zone_name': new_zone.name,
                'new_zone_id': new_zone.id,
                'old_zone_name': old_zone_name,
                'old_zone_id': old_zone_id,
                'already_in_zone': True,
                'garden_zones': [{'id': z.id, 'name': z.name} for z in garden_zones]
            })

        # Check if the plant's current status is available in the target zone
        current_status = plant.status
        target_zone_statuses = new_zone.get_plant_statuses()
        if current_status not in target_zone_statuses:
            print(f"Plant status '{current_status}' not available in target zone {zone_id}")
            garden_zones = [z for z in new_zone.garden.zones]
            return jsonify({
                'success': False,
                'error': f"Cannot move plant to {new_zone.name}. The plant's current status '{current_status}' is not available in the target zone.",
                'plant_id': plant_id,
                'plant_name': plant_name,
                'new_zone_name': new_zone.name,
                'new_zone_id': new_zone.id,
                'old_zone_name': old_zone_name,
                'old_zone_id': old_zone_id,
                'status_mismatch': True,
                'current_status': current_status,
                'available_statuses': target_zone_statuses
            }), 400

        # Move the plant
        plant.zone_id = zone_id

        # Update the timestamp with correct timezone
        current_garden.last_updated = now_in_timezone()
        new_garden.last_updated = now_in_timezone()

        db.session.commit()

        # Generate HTML for the plant in its new zone
        from flask import render_template_string

        # Get the plant's status and style
        status = plant.status
        status_index = new_zone.get_plant_statuses().index(status) if status in new_zone.get_plant_statuses() else 0
        color_sequence = [
            {'bg': 'bg-success text-white', 'color': '#28a745'},
            {'bg': 'bg-info text-white', 'color': '#17a2b8'},
            {'bg': 'bg-primary text-white', 'color': '#4e73df'},
            {'bg': 'bg-warning text-white', 'color': '#ffc107'},
            {'bg': 'bg-pink text-white', 'color': '#e83e8c'},
            {'bg': 'bg-orange text-white', 'color': '#fd7e14'},
            {'bg': 'bg-teal text-white', 'color': '#20c997'},
            {'bg': 'bg-purple text-white', 'color': '#6f42c1'},
            {'bg': 'bg-cyan text-white', 'color': '#17a2b8'},
            {'bg': 'bg-indigo text-white', 'color': '#6610f2'}
        ]
        status_icons = {
            'Seedling': 'seedling',
            'Growing': 'leaf',
            'Mature': 'tree',
            'Harvesting': 'cut',
            'Dormant': 'moon',
            'Flowering': 'flower',
            'Fruiting': 'apple-alt',
            'Transplanted': 'exchange-alt',
            'Diseased': 'biohazard',
            'Completed': 'check-circle'
        }
        color_index = status_index % len(color_sequence)
        style = {
            'bg': color_sequence[color_index]['bg'],
            'icon': status_icons.get(status, 'circle'),
            'extra_style': f"background-color: {color_sequence[color_index]['color']} !important;"
        }

        # Get the plant's tracking info for timestamp
        latest_tracking = PlantTracking.query.filter_by(plant_id=plant.id)\
            .order_by(PlantTracking.date_logged.desc())\
            .first()
        timestamp = latest_tracking.date_logged if latest_tracking else now_in_timezone()

        # Get all zones in the garden for move dropdown
        garden_zones = [z for z in new_zone.garden.zones]

        # Template for a single plant row
        plant_row_template = '''
        <div class="plant-row d-flex align-items-center py-2 px-4 border-bottom"
             style="border-color: rgba(28, 200, 138, 0.1) !important;
                    transition: background-color 0.2s ease;">
            <!-- Plant Name & Variety -->
            <div class="col-3 d-flex align-items-center gap-2">
                <span style="color: #1cc88a; font-weight: 500;">
                    {{ plant.plant_detail.name }}
                </span>
                {% if plant.variety %}
                <small class="text-muted">{{ plant.variety.name }}</small>
                {% endif %}
            </div>

            <!-- Quantity -->
            <div class="col-2">
                <span class="badge bg-light text-success">
                    <i class="fas fa-seedling"></i> {{ plant.quantity }}
                </span>
            </div>

            <!-- Status -->
            <div class="col-3 d-flex">
                <span class="badge {{ style.bg }} d-inline-flex align-items-center gap-1"
                      style="font-size: 0.8rem;
                             padding: 0.35rem 0.75rem;
                             {{ style.extra_style }}
                             white-space: nowrap;
                             max-width: fit-content;">
                    <i class="fas fa-{{ style.icon }}"></i>
                    {{ plant.status }}
                </span>
            </div>

            <!-- Last Updated -->
            <div class="col-2 text-muted">
                <small>
                    <i class="far fa-clock me-1"></i>
                    just now
                </small>
            </div>

            <!-- Actions -->
            <div class="col-2 d-flex gap-1">
                <div class="dropdown">
                    <button class="btn btn-sm btn-light px-2 py-1" data-bs-toggle="dropdown">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end">
                        {% for status in new_zone.get_plant_statuses() %}
                        <li>
                            {% if status == plant.status %}
                            <!-- Current status - not clickable -->
                            <span class="dropdown-item py-1 text-muted d-flex align-items-center">
                                <i class="fas fa-check me-2 text-success"></i>
                                {{ status }}
                            </span>
                            {% else %}
                            <!-- Other statuses - clickable -->
                            <a class="dropdown-item py-1 status-update-link"
                               href="#"
                               data-plant-id="{{ plant.id }}"
                               data-status="{{ status }}"
                               data-csrf-token="{{ csrf_token }}">
                                {{ status }}
                            </a>
                            {% endif %}
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                {% if garden_zones|length > 1 %}
                <div class="dropdown">
                    <button class="btn btn-sm btn-light px-2 py-1" data-bs-toggle="dropdown">
                        <i class="fas fa-exchange-alt"></i>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end">
                        {% for available_zone in garden_zones %}
                            {% if available_zone.id != plant.zone_id %}
                            <li>
                                <a class="dropdown-item py-1 move-plant-link"
                                   href="#"
                                   data-plant-id="{{ plant.id }}"
                                   data-zone-id="{{ available_zone.id }}"
                                   data-zone-name="{{ available_zone.name }}"
                                   data-csrf-token="{{ csrf_token }}">
                                    {{ available_zone.name }}
                                </a>
                            </li>
                            {% endif %}
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}
            </div>
        </div>
        '''

        # Render the plant row HTML
        from flask_wtf.csrf import generate_csrf
        csrf_token = generate_csrf()
        print(f"Generated new CSRF token: {csrf_token}")

        plant_html = render_template_string(
            plant_row_template,
            plant=plant,
            style=style,
            timestamp=timestamp,
            new_zone=new_zone,
            garden_zones=garden_zones,
            csrf_token=csrf_token
        )

        return jsonify({
            'success': True,
            'message': f'Moved {plant_name} from {old_zone_name} to {new_zone.name}!',
            'plant_id': plant_id,
            'plant_name': plant_name,
            'new_zone_name': new_zone.name,
            'new_zone_id': new_zone.id,
            'old_zone_name': old_zone_name,
            'old_zone_id': old_zone_id,
            'plant_html': plant_html,
            'garden_zones': [{'id': z.id, 'name': z.name} for z in garden_zones],
            'csrf_token': csrf_token
        })
    except Exception as e:
        db.session.rollback()
        error_message = str(e)
        print(f"Error moving plant: {error_message}")
        import traceback
        traceback.print_exc()

        # Add more context to common errors
        if "already in zone" in error_message.lower():
            error_message = f"Plant is already in this zone. {error_message}"
        elif "permission denied" in error_message.lower():
            error_message = f"You don't have permission to move this plant. {error_message}"
        elif "not found" in error_message.lower():
            error_message = f"Plant or zone not found. {error_message}"
        elif "string did not match" in error_message.lower() or "expected pattern" in error_message.lower():
            error_message = f"Invalid data format. Please try again. {error_message}"

        return jsonify({
            'success': False,
            'error': error_message,
            'exception_type': e.__class__.__name__
        }), 500


@gardens.route("/garden/<int:garden_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_garden(garden_id):
    garden = Garden.query.get_or_404(garden_id)
    if garden.owner_id != current_user.id:  # Changed from garden.owner to garden.owner_id
        abort(403)
    form = GardenForm()
    form.garden_id = garden_id  # For validation

    if form.validate_on_submit():
        if form.name.data:  # Only update name if provided
            garden.name = form.name.data
        if form.location.data:  # Only update location if provided
            garden.location = form.location.data

        # Garden members are handled via AJAX, so we don't update them here

        db.session.commit()
        flash('Your garden has been updated!', 'success')
        return redirect(url_for('gardens.view_gardens'))
    elif request.method == 'GET':
        form.name.data = garden.name
        form.location.data = garden.location

    return render_template('edit_page_gardens.html', form=form, garden=garden)


@gardens.route("/api/users/search", methods=['GET'])
@login_required
def search_users():
    """Search for users by name or username"""
    query = request.args.get('query', '')
    if not query or len(query) < 2:
        return jsonify({'users': []})

    # Search for users matching the query
    users = User.query.filter(
        (User.username.ilike(f'%{query}%')) |
        (User.firstName.ilike(f'%{query}%')) |
        (User.lastName.ilike(f'%{query}%')) |
        (User.email.ilike(f'%{query}%'))
    ).limit(10).all()

    # Format the results
    results = [{
        'id': user.id,
        'username': user.username,
        'name': f"{user.firstName} {user.lastName}",
        'email': user.email,
        'image': user.image_file
    } for user in users]

    return jsonify({'users': results})


@gardens.route("/api/garden/<int:garden_id>/members", methods=['GET'])
@login_required
def get_garden_members(garden_id):
    """Get all members of a garden"""
    garden = Garden.query.get_or_404(garden_id)

    # Check if user has access to this garden
    if current_user not in garden.members and current_user.id != garden.owner_id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Format the members
    members = [{
        'id': member.id,
        'username': member.username,
        'name': f"{member.firstName} {member.lastName}",
        'email': member.email,
        'image': member.image_file,
        'isOwner': member.id == garden.owner_id
    } for member in garden.members]

    return jsonify({'members': members})


@gardens.route("/api/garden/<int:garden_id>/members/<int:user_id>", methods=['POST'])
@login_required
def add_garden_member(garden_id, user_id):
    """Add a user to a garden's members"""
    garden = Garden.query.get_or_404(garden_id)

    # Only the owner can add members
    if garden.owner_id != current_user.id:
        return jsonify({'error': 'Only the garden owner can add members'}), 403

    user = User.query.get_or_404(user_id)

    # Check if user is already a member
    if user in garden.members:
        return jsonify({'message': 'User is already a member of this garden'})

    # Add the user to the garden
    garden.members.append(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'{user.firstName} {user.lastName} added to garden',
        'member': {
            'id': user.id,
            'username': user.username,
            'name': f"{user.firstName} {user.lastName}",
            'email': user.email,
            'image': user.image_file,
            'isOwner': user.id == garden.owner_id
        }
    })


@gardens.route("/api/garden/<int:garden_id>/members/<int:user_id>", methods=['DELETE'])
@login_required
def remove_garden_member(garden_id, user_id):
    """Remove a user from a garden's members"""
    garden = Garden.query.get_or_404(garden_id)

    # Only the owner can remove members
    if garden.owner_id != current_user.id:
        return jsonify({'error': 'Only the garden owner can remove members'}), 403

    # Cannot remove the owner
    if user_id == garden.owner_id:
        return jsonify({'error': 'Cannot remove the garden owner'}), 400

    user = User.query.get_or_404(user_id)

    # Check if user is a member
    if user not in garden.members:
        return jsonify({'error': 'User is not a member of this garden'}), 404

    # Remove the user from the garden
    garden.members.remove(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'{user.firstName} {user.lastName} removed from garden'
    })


@gardens.route("/garden/<int:garden_id>/delete", methods=['POST'])
@login_required
def delete_garden(garden_id):
    print(f"Delete garden route called for garden_id: {garden_id}")  # Debug log

    # Get the garden or return 404
    garden = Garden.query.get_or_404(garden_id)

    print(f"Current user id: {current_user.id}")  # Debug log
    print(f"Garden owner id: {garden.owner_id}")  # Debug log

    # Check if user is the owner of the garden
    if garden.owner_id != current_user.id:
        print("Permission denied - user is not owner")  # Debug log
        abort(403)

    try:
        # First, delete all plants and their related data in all zones
        for zone in garden.zones:
            # Get all plants in this zone
            plants = Plant.query.filter_by(zone_id=zone.id).all()

            for plant in plants:
                # Delete plant tracking records
                PlantTracking.query.filter_by(plant_id=plant.id).delete()
                print(f"Deleted tracking records for plant {plant.id}")

                # Delete harvests
                Harvest.query.filter_by(plant_id=plant.id).delete()
                print(f"Deleted harvests for plant {plant.id}")

                # Delete the plant itself
                db.session.delete(plant)
                print(f"Deleted plant {plant.id}")

            # Delete the zone
            db.session.delete(zone)
            print(f"Deleted zone {zone.id}")

        # Remove all garden-user associations
        garden.members = []
        print("Removed all garden members")

        # Finally delete the garden
        db.session.delete(garden)
        print("Garden marked for deletion")

        db.session.commit()
        print("Garden and all related data deleted successfully")

        flash('Your garden and all its contents have been deleted!', 'success')
        return redirect(url_for('gardens.view_gardens'))

    except Exception as e:
        print(f"Error deleting garden: {str(e)}")  # Debug log
        db.session.rollback()
        flash('Error deleting garden. Please try again.', 'danger')
        return redirect(url_for('gardens.view_gardens'))


@gardens.route("/zone/<int:zone_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_zone(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    garden = Garden.query.get(zone.garden_id)

    # Check permissions
    if garden.owner_id != current_user.id:
        abort(403)

    form = ZoneForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            # Update zone name
            zone.name = form.name.data

            # Get statuses from form
            statuses = []
            for status_field in form.plant_statuses:
                if status_field.data and status_field.data.strip():
                    statuses.append(status_field.data.strip())

            # Remove duplicates while preserving order
            statuses = list(dict.fromkeys(statuses))

            print("Submitted statuses:", statuses)  # Debug print

            if statuses:
                try:
                    zone.set_plant_statuses(statuses)
                    db.session.commit()
                    flash('Zone has been updated successfully!', 'success')
                    return redirect(url_for('gardens.view_gardens'))
                except Exception as e:
                    print(f"Error saving statuses: {e}")  # Debug print
                    db.session.rollback()
                    flash('Error updating zone statuses.', 'danger')
            else:
                flash('At least one plant status is required.', 'danger')

    # GET request or form validation failed
    form.name.data = zone.name
    current_statuses = zone.get_plant_statuses()
    print("Current zone statuses:", current_statuses)  # Debug print
    form.load_zone_statuses(zone)

    return render_template('edit_zone.html',
                         title='Edit Zone',
                         form=form,
                         zone=zone)  # Add garden to template context


@gardens.route("/zone/<int:zone_id>/delete", methods=['POST'])
@login_required
def delete_zone(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    garden = Garden.query.get(zone.garden_id)

    # Check if user is the owner of the garden
    if garden.owner_id != current_user.id:
        abort(403)

    # Delete all plants in the zone
    Plant.query.filter_by(zone_id=zone.id).delete()

    # Delete the zone
    db.session.delete(zone)
    garden.last_updated = now_in_timezone()
    db.session.commit()

    flash('Your zone has been deleted!', 'success')
    return redirect(url_for('gardens.view_gardens'))


@gardens.route("/garden/<int:garden_id>/zone/<int:zone_id>/add_plant", methods=['GET', 'POST'])
@login_required
def add_plant(garden_id, zone_id):
    garden = Garden.query.get_or_404(garden_id)
    zone = Zone.query.get_or_404(zone_id)

    # Check if user is a member of the garden
    if current_user not in garden.members:
        abort(403)

    form = PlantForm(data={'plant_detail_id': request.form.get('plant_detail_id')})

    if form.validate_on_submit():
        plant_detail = PlantDetail.query.get(form.plant_detail_id.data)
        if not plant_detail:
            flash('Invalid plant selection.', 'danger')
            return redirect(url_for('gardens.add_plant', garden_id=garden_id, zone_id=zone_id))

        try:
            plant = Plant(
                plant_detail_id=form.plant_detail_id.data,
                variety_id=form.variety_id.data if form.variety_id.data != -1 else None,
                quantity=form.quantity.data,
                planting_date=form.planting_date.data,
                zone_id=zone_id
            )

            # If it's a new variety, create it
            if form.variety_id.data == -1 and request.form.get('variety_name'):
                new_variety = PlantVariety(
                    name=request.form.get('variety_name'),
                    plant_detail_id=form.plant_detail_id.data
                )
                db.session.add(new_variety)
                db.session.flush()  # Get the new variety ID
                plant.variety_id = new_variety.id

            db.session.add(plant)
            db.session.flush()  # Ensure plant has an ID

            # Set initial status
            plant.set_initial_status('Seedling', 'Initial plant status')

            db.session.commit()
            flash('Plant added successfully!', 'success')
            return redirect(url_for('gardens.view_gardens'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding plant: {str(e)}', 'danger')
            return redirect(url_for('gardens.add_plant', garden_id=garden_id, zone_id=zone_id))

    # If form validation fails, print the errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')

    return render_template('add_plant.html', form=form, garden=garden, zone=zone)


@gardens.route("/gardens/get_varieties/<int:plant_detail_id>")
@login_required
def get_varieties(plant_detail_id):
    plant_detail = PlantDetail.query.get_or_404(plant_detail_id)
    varieties = [{"id": v.id, "name": v.name} for v in plant_detail.varieties]
    return jsonify({"varieties": varieties})


@gardens.route("/plant/<int:plant_id>/debug")
@login_required
def debug_plant_status(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    tracking_entries = PlantTracking.query.filter_by(plant_id=plant.id)\
        .order_by(PlantTracking.date_logged.desc()).all()

    debug_info = {
        'plant_id': plant.id,
        'current_status': plant.status,
        'tracking_history': [
            {
                'stage': entry.stage,
                'date': entry.date_logged,
                'notes': entry.notes
            }
            for entry in tracking_entries
        ]
    }
    return jsonify(debug_info)


@gardens.route("/plant/<int:plant_id>/status/<status>")
@login_required
def update_plant_status(plant_id, status):
    plant = Plant.query.get_or_404(plant_id)
    zone = Zone.query.get(plant.zone_id)
    garden = Garden.query.get(zone.garden_id)

    # Ensure user has permission
    if current_user not in garden.members:
        abort(403)

    # Verify the status is valid for this zone
    if status not in zone.get_plant_statuses():
        abort(400)

    plant.update_status(status, notes=f"Status updated to {status}")
    garden.last_updated = now_in_timezone()
    db.session.commit()

    flash('Plant status updated successfully!', 'success')
    return redirect(url_for('gardens.view_gardens'))


@gardens.route("/api/plant/<int:plant_id>/status/<status>", methods=['POST'])
@login_required
def update_plant_status_ajax(plant_id, status):
    plant = Plant.query.get_or_404(plant_id)
    zone = Zone.query.get(plant.zone_id)
    garden = Garden.query.get(zone.garden_id)

    # Ensure user has permission
    if current_user not in garden.members:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403

    # Verify the status is valid for this zone
    if status not in zone.get_plant_statuses():
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

    try:
        plant.update_status(status, notes=f"Status updated to {status}")
        garden.last_updated = now_in_timezone()
        db.session.commit()

        # Get the status style information for the response
        status_index = zone.get_plant_statuses().index(status) if status in zone.get_plant_statuses() else 0
        color_sequence = [
            {'bg': 'bg-success text-white', 'color': '#28a745'},
            {'bg': 'bg-info text-white', 'color': '#17a2b8'},
            {'bg': 'bg-primary text-white', 'color': '#4e73df'},
            {'bg': 'bg-warning text-white', 'color': '#ffc107'},
            {'bg': 'bg-pink text-white', 'color': '#e83e8c'},
            {'bg': 'bg-orange text-white', 'color': '#fd7e14'},
            {'bg': 'bg-teal text-white', 'color': '#20c997'},
            {'bg': 'bg-purple text-white', 'color': '#6f42c1'},
            {'bg': 'bg-cyan text-white', 'color': '#17a2b8'},
            {'bg': 'bg-indigo text-white', 'color': '#6610f2'}
        ]
        status_icons = {
            'Seedling': 'seedling',
            'Growing': 'leaf',
            'Mature': 'tree',
            'Harvesting': 'cut',
            'Dormant': 'moon',
            'Flowering': 'flower',
            'Fruiting': 'apple-alt',
            'Transplanted': 'exchange-alt',
            'Diseased': 'biohazard',
            'Completed': 'check-circle'
        }
        color_index = status_index % len(color_sequence)
        style = {
            'bg': color_sequence[color_index]['bg'],
            'icon': status_icons.get(status, 'circle'),
            'extra_style': f"background-color: {color_sequence[color_index]['color']} !important;"
        }

        # Get the latest tracking record for timestamp
        latest_tracking = PlantTracking.query.filter_by(plant_id=plant.id)\
            .order_by(PlantTracking.date_logged.desc())\
            .first()

        # Get the timestamp for the response
        timestamp = latest_tracking.date_logged.isoformat() if latest_tracking else now_in_timezone().isoformat()
        timestamp_display = 'just now'

        # Get all valid statuses for this zone
        valid_statuses = zone.get_plant_statuses()

        return jsonify({
            'success': True,
            'status': status,
            'style': style,
            'message': 'Plant status updated successfully!',
            'timestamp': timestamp,
            'timestamp_display': timestamp_display,
            'valid_statuses': valid_statuses
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
