from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import current_user, login_required
from greenbyte import db
from greenbyte.gardens.forms import GardenForm, ZoneForm
from greenbyte.models import Garden, Zone

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


@gardens.route('/gardenHome')
def gardenHome():
    gardens = Garden.query.all()
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