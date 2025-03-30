from flask import Blueprint, render_template, abort, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from greenbyte import db
from greenbyte.models import (
    User, Garden, Zone, Plant, PlantTracking, Post, PostImage, PostPlant,
    Harvest, Client, Order, OrderItem, Delivery, Payment, Address, ZoneType,
    GrowingMethod, PlantDetail, Variety
)
from sqlalchemy import inspect
from flask_bcrypt import Bcrypt

admin = Blueprint('admin', __name__)
bcrypt = Bcrypt()

@admin.route("/admin/create/<string:model_name>", methods=['POST'])
@login_required
def create_record(model_name):
    if current_user.access_level not in ['admin', 'superadmin']:
        abort(403)

    models = {
        'Users': User,
        'Gardens': Garden,
        'Zones': Zone,
        'Plants': Plant,
        'Plant_Tracking': PlantTracking,
        'Posts': Post,
        'Post_Images': PostImage,
        'Post_Plants': PostPlant,
        'Harvests': Harvest,
        'Clients': Client,
        'Orders': Order,
        'Order_Items': OrderItem,
        'Deliveries': Delivery,
        'Payments': Payment,
        'Addresses': Address,
        'Zone_Types': ZoneType,
        'Growing_Methods': GrowingMethod,
        'Plant_Details': PlantDetail,
        'Varieties': Variety
    }

    model = models.get(model_name)
    if not model:
        return jsonify({'error': 'Invalid model name'}), 400

    try:
        data = request.json
        
        # Special handling for User model (password hashing)
        if model == User and 'password' in data:
            data['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        # Create new instance
        new_record = model(**data)
        db.session.add(new_record)
        db.session.commit()
        
        return jsonify({'message': f'New {model_name} record created successfully'}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin.route("/make_admin/<int:user_id>")
@login_required
def make_admin(user_id):
    # Only super admins can create other admins
    if not current_user.access_level == 'superadmin':
        abort(403)
    
    user = User.query.get_or_404(user_id)
    user.access_level = 'admin'
    db.session.commit()
    flash(f'User {user.username} has been promoted to admin', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin.route("/admin")
@login_required
def admin_dashboard():
    if current_user.access_level not in ['admin', 'superadmin']:
        abort(403)  # Forbidden
    
    # Get all models
    models = {
        'Users': User,
        'Gardens': Garden,
        'Zones': Zone,
        'Plants': Plant,
        'Plant_Tracking': PlantTracking,
        'Posts': Post,
        'Post_Images': PostImage,
        'Post_Plants': PostPlant,
        'Harvests': Harvest,
        'Clients': Client,
        'Orders': Order,
        'Order_Items': OrderItem,
        'Deliveries': Delivery,
        'Payments': Payment,
        'Addresses': Address,
        'Zone_Types': ZoneType,
        'Growing_Methods': GrowingMethod,
        'Plant_Details': PlantDetail,
        'Varieties': Variety
    }
    
    # Get data for each model
    tables_data = {}
    for table_name, model in models.items():
        # Get column names and types
        inspector = inspect(model)
        columns = []
        for column in inspector.columns:
            col_type = str(column.type)
            # Skip certain columns in create form
            if column.name not in ['id', 'created_at', 'updated_at']:
                columns.append({
                    'name': column.name,
                    'type': col_type,
                    'nullable': column.nullable,
                    'foreign_key': column.foreign_keys is not None and len(column.foreign_keys) > 0
                })
        
        # Get all records
        records = model.query.all()
        
        # Convert records to dictionaries
        data = []
        for record in records:
            row = {}
            for column in inspector.columns:
                row[column.name] = getattr(record, column.name)
            data.append(row)
            
        tables_data[table_name] = {
            'columns': columns,
            'data': data
        }
    
    return render_template('admin/dashboard.html', tables_data=tables_data)

@admin.route("/check_access")
@login_required
def check_access():
    if current_user.is_authenticated:
        return f"Access level: {current_user.access_level}, Email: {current_user.email}"
    return "Not logged in"
