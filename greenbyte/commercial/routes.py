from flask import render_template, flash, redirect, url_for, request, jsonify, abort
from greenbyte import db
from greenbyte.commercial import commercial
from greenbyte.models import Farm, User
from greenbyte.commercial.forms import FarmForm
from flask_login import current_user, login_required

@commercial.route("/commercial/dashboard")
@commercial.route("/commercial/dashboard/<int:farm_id>")
@login_required
def dashboard(farm_id=None):
    """Commercial Dashboard page."""
    # Get user's farms
    user_farms = current_user.farms
    owned_farms = current_user.owned_farms

    # If no farm_id is provided, use the first farm the user has access to
    selected_farm = None
    if farm_id:
        selected_farm = Farm.query.get_or_404(farm_id)
        # Check if user has access to this farm
        if selected_farm.owner_id != current_user.id and not current_user.is_farm_admin(farm_id) and not current_user.is_farm_gardener(farm_id):
            abort(403)  # Forbidden
    elif owned_farms:
        selected_farm = owned_farms[0]
    elif user_farms:
        selected_farm = user_farms[0]

    # Set the title based on whether a farm is selected
    title = f'Farm Dashboard: {selected_farm.name}' if selected_farm else 'Commercial Dashboard'

    return render_template('commercial/dashboard.html', title=title,
                           user_farms=user_farms, owned_farms=owned_farms, selected_farm=selected_farm)

@commercial.route("/commercial/farms/create", methods=['GET', 'POST'])
@login_required
def create_farm():
    """Create a new farm."""
    # Check if user is a super user who can create farms
    if not current_user.is_super_user():
        flash('You do not have permission to create farms.', 'danger')
        return redirect(url_for('commercial.dashboard'))

    form = FarmForm()

    if form.validate_on_submit():
        # Create new farm
        farm = Farm(
            name=form.name.data,
            location=form.location.data,
            description=form.description.data,
            business_name=form.business_name.data,
            tax_id=form.tax_id.data,
            phone=form.phone.data,
            email=form.email.data,
            website=form.website.data,
            owner_id=current_user.id
        )

        db.session.add(farm)
        db.session.commit()

        flash(f'Farm "{farm.name}" has been created!', 'success')
        return redirect(url_for('commercial.farm', farm_id=farm.id))

    return render_template('commercial/create_farm.html', title='Create Farm', form=form)

@commercial.route("/commercial/clients")
@login_required
def clients():
    """Client Management page."""
    return render_template('commercial/clients_improved.html', title='Client Management')

@commercial.route("/commercial/products")
@login_required
def products():
    """Product Management page."""
    return render_template('commercial/products.html', title='Product Management')

@commercial.route("/commercial/test")
@login_required
def test():
    """Test page for jQuery."""
    return render_template('commercial/test.html', title='jQuery Test')

@commercial.route("/commercial/orders")
@login_required
def orders():
    """Order Management page."""
    return render_template('commercial/orders.html', title='Order Management')

@commercial.route("/commercial/deliveries")
@login_required
def deliveries():
    """Delivery Management page."""
    return render_template('commercial/deliveries.html', title='Delivery Management')

@commercial.route("/commercial/invoices")
@login_required
def invoices():
    """Invoice Management page."""
    return render_template('commercial/invoices.html', title='Invoice Management')

@commercial.route("/commercial/farm/<int:farm_id>")
@login_required
def farm(farm_id):
    """Farm detail page."""
    farm = Farm.query.get_or_404(farm_id)

    # Check if user has access to this farm
    if farm.owner_id != current_user.id and not current_user.is_farm_admin(farm_id) and not current_user.is_farm_gardener(farm_id):
        abort(403)  # Forbidden

    return render_template('commercial/farm.html', title=f'Farm: {farm.name}', farm=farm)

@commercial.route("/commercial/farm/<int:farm_id>/add_member", methods=['POST'])
@login_required
def add_farm_member(farm_id):
    """Add a member to a farm."""
    farm = Farm.query.get_or_404(farm_id)

    # Check if user has permission to add members
    if farm.owner_id != current_user.id and not current_user.is_farm_admin(farm_id):
        return jsonify({'success': False, 'message': 'You do not have permission to add members to this farm'}), 403

    # Get data from request
    data = request.get_json()
    email = data.get('email')
    role = data.get('role', 'gardener')

    # Validate role
    if role not in ['admin', 'gardener']:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400

    # Find user by email
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    # Check if user is already a member
    if farm.get_member_role(user.id):
        return jsonify({'success': False, 'message': 'User is already a member of this farm'}), 400

    # Add user to farm
    try:
        farm.add_member(user, role)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@commercial.route("/commercial/farm/<int:farm_id>/update_member_role", methods=['POST'])
@login_required
def update_farm_member_role(farm_id):
    """Update a member's role in a farm."""
    farm = Farm.query.get_or_404(farm_id)

    # Check if user has permission to update member roles
    if farm.owner_id != current_user.id and not current_user.is_farm_admin(farm_id):
        return jsonify({'success': False, 'message': 'You do not have permission to update member roles in this farm'}), 403

    # Get data from request
    data = request.get_json()
    member_id = data.get('member_id')
    role = data.get('role')

    # Validate role
    if role not in ['admin', 'gardener']:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400

    # Find user
    user = User.query.get(member_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    # Update role
    try:
        farm.add_member(user, role)  # This will update the role if the user is already a member
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@commercial.route("/commercial/farm/<int:farm_id>/remove_member", methods=['POST'])
@login_required
def remove_farm_member(farm_id):
    """Remove a member from a farm."""
    farm = Farm.query.get_or_404(farm_id)

    # Check if user has permission to remove members
    if farm.owner_id != current_user.id and not current_user.is_farm_admin(farm_id):
        return jsonify({'success': False, 'message': 'You do not have permission to remove members from this farm'}), 403

    # Get data from request
    data = request.get_json()
    member_id = data.get('member_id')

    # Find user
    user = User.query.get(member_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    # Cannot remove the owner
    if user.id == farm.owner_id:
        return jsonify({'success': False, 'message': 'Cannot remove the farm owner'}), 400

    # Remove user from farm
    try:
        farm.remove_member(user)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@commercial.route("/commercial/farm/<int:farm_id>/update", methods=['POST'])
@login_required
def update_farm(farm_id):
    """Update farm information."""
    farm = Farm.query.get_or_404(farm_id)

    # Check if user has permission to update farm
    if farm.owner_id != current_user.id and not current_user.is_farm_admin(farm_id):
        return jsonify({'success': False, 'message': 'You do not have permission to update this farm'}), 403

    # Get data from request
    data = request.get_json()

    # Update farm fields
    try:
        farm.name = data.get('name', farm.name)
        farm.business_name = data.get('business_name')
        farm.location = data.get('location')
        farm.phone = data.get('phone')
        farm.email = data.get('email')
        farm.website = data.get('website')
        farm.tax_id = data.get('tax_id')
        farm.description = data.get('description')

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
