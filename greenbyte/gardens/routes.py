from flask import Blueprint, render_template, flash, redirect, url_for, abort
from flask_login import current_user, login_required
from greenbyte import db
from greenbyte.gardens.forms import GardenForm, ZoneForm
from greenbyte.models import Garden, Zone, user_garden, User, Plant, PlantTracking, Harvest
from datetime import datetime, timedelta
from flask import current_app
from greenbyte.utils.timezone import now_in_timezone, localize_datetime

gardens = Blueprint('gardens', __name__)

@gardens.route("/garden/new", methods=['GET', 'POST'])
@login_required
def create_garden():
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
        return redirect(url_for('main.index'))
    return render_template('create_garden.html', form=form)


@gardens.route("/gardens")
@login_required
def view_gardens():
    gardens = Garden.query.join(user_garden).filter(
        user_garden.c.user_id == current_user.id
    ).order_by(Garden.last_updated.desc()).all()
    
    return render_template('gardens.html', gardens=gardens)


@gardens.route('/add_zone', methods=['GET', 'POST'])
@login_required
def add_zone():
    # Fetch gardens where the current user is a member
    user_gardens = current_user.gardens
    form = ZoneForm(user_gardens)
    if form.validate_on_submit():
        # Create a new zone
        zone = Zone(
            name=form.name.data,
            garden_id=form.garden.data  # Selected garden ID from the form
        )
        db.session.add(zone)
        db.session.commit()
        flash('Zone added successfully!', 'success')
        return redirect(url_for('gardens.gardenHome'))
    return render_template('add_zone.html', form=form)


@gardens.route("/plant/<int:plant_id>/status/<string:status>")
@login_required
def update_plant_status(plant_id, status):
    plant = Plant.query.get_or_404(plant_id)
    
    # Get the garden through the plant's zone
    zone = Zone.query.get(plant.zone_id)
    garden = Garden.query.get(zone.garden_id)
    
    if not garden or not current_user in garden.members:
        abort(403)
    
    # Update the plant status
    plant.status = status
    
    # Update the garden's last_updated timestamp
    garden.last_updated = now_in_timezone()
    
    db.session.commit()
    
    flash(f'Plant status updated to {status}!', 'success')
    return redirect(url_for('gardens.view_gardens'))


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
    
    flash(f'Moved {plant.name} from {old_zone} to {new_zone.name}!', 'success')
    return redirect(url_for('gardens.view_gardens'))
