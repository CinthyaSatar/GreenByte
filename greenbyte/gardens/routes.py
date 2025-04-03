
from flask import Blueprint, render_template, flash, redirect, url_for, abort, request, jsonify
from flask_login import current_user, login_required
from greenbyte import db
from greenbyte.gardens.forms import GardenForm, ZoneForm, PlantForm
from greenbyte.models import (
    Garden, Zone, Plant, PlantTracking,
    Harvest, user_garden, PlantDetail, PlantVariety
)
from datetime import datetime, timedelta
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

        db.session.add(garden)
        db.session.commit()

        # Create default zone
        db.session.commit()

        flash('Your garden has been created!', 'success')
        return redirect(url_for('gardens.view_gardens'))

    return render_template('add_garden.html',
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

    return render_template('gardens.html',
                         gardens=gardens,
                         status_style_mapping=status_style_mapping,
                         default_style=default_style)


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

    # Move the plant
    old_zone = plant.zone.name
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

        # Move the plant
        plant.zone_id = zone_id

        # Update the timestamp with correct timezone
        current_garden.last_updated = now_in_timezone()
        new_garden.last_updated = now_in_timezone()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Moved {plant_name} from {old_zone_name} to {new_zone.name}!',
            'plant_id': plant_id,
            'plant_name': plant_name,
            'new_zone_name': new_zone.name,
            'new_zone_id': new_zone.id,
            'old_zone_name': old_zone_name,
            'old_zone_id': old_zone_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


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
        db.session.commit()
        flash('Your garden has been updated!', 'success')
        return redirect(url_for('gardens.view_gardens'))
    elif request.method == 'GET':
        form.name.data = garden.name
        form.location.data = garden.location

    return render_template('edit_garden.html', form=form, garden=garden)


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

        return jsonify({
            'success': True,
            'status': status,
            'style': style,
            'message': 'Plant status updated successfully!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
