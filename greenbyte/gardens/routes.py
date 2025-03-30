
from flask import Blueprint, render_template, flash, redirect, url_for, abort, request, jsonify
from flask_login import current_user, login_required
from greenbyte import db
from greenbyte.gardens.forms import GardenForm, ZoneForm, PlantForm
from greenbyte.models import (
    Garden, Zone, user_garden, User, Plant, PlantTracking, 
    Harvest, PlantDetail, PlantVariety  # Changed Variety to PlantVariety
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
        garden.members.append(current_user)  # Add the creator as a member
        db.session.add(garden)
        db.session.commit()
        flash('Your garden has been created!', 'success')
        return redirect(url_for('gardens.view_gardens'))  # Changed from 'main.index'
    return render_template('add_garden.html', form=form)


@gardens.route("/gardens")
@login_required
def view_gardens():
    gardens = Garden.query.join(user_garden).filter(
        user_garden.c.user_id == current_user.id
    ).order_by(Garden.last_updated.desc()).all()
    
    return render_template('gardens.html', gardens=gardens)


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
        flash('Zone added successfully!', 'success')
        return redirect(url_for('gardens.view_gardens'))
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


@gardens.route("/garden/<int:garden_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_garden(garden_id):
    garden = Garden.query.get_or_404(garden_id)
    
    # Check if user is the owner of the garden
    if garden.owner_id != current_user.id:
        abort(403)
    
    form = GardenForm()
    if form.validate_on_submit():
        garden.name = form.name.data
        garden.location = form.location.data
        garden.last_updated = now_in_timezone()
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
    garden = Garden.query.get_or_404(garden_id)
    
    # Check if user is the owner of the garden
    if garden.owner_id != current_user.id:
        abort(403)
    
    # Delete all zones associated with this garden
    Zone.query.filter_by(garden_id=garden.id).delete()
    
    # Delete the garden
    db.session.delete(garden)
    db.session.commit()
    
    flash('Your garden has been deleted!', 'success')
    return redirect(url_for('gardens.view_gardens'))


@gardens.route("/zone/<int:zone_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_zone(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    garden = Garden.query.get(zone.garden_id)
    
    # Check if user is a member of the garden
    if current_user not in garden.members:
        abort(403)
    
    form = ZoneForm()
    if form.validate_on_submit():
        zone.name = form.name.data
        garden.last_updated = now_in_timezone()
        db.session.commit()
        flash('Your zone has been updated!', 'success')
        return redirect(url_for('gardens.view_gardens'))
    elif request.method == 'GET':
        form.name.data = zone.name
    return render_template('edit_zone.html', form=form, zone=zone, garden=garden)


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
