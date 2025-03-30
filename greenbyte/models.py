from datetime import datetime, timedelta
from itsdangerous import Serializer, BadSignature, SignatureExpired
from greenbyte import db, login_manager
from flask_login import UserMixin
from flask import current_app
from sqlalchemy_utils import TimezoneType
from .utils.timezone import now_in_timezone, get_current_timezone

@login_manager.user_loader
def loadUser(userId):
    return User.query.get(int(userId))

# Many-to-Many Relationship for Users and Gardens
user_garden = db.Table('user_garden',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('garden_id', db.Integer, db.ForeignKey('garden.id'), primary_key=True),
    db.Column('role', db.String(20), nullable=False, default='member')  # 'member', 'commercial', 'manager'
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    firstName = db.Column(db.String(25), nullable=False)
    lastName = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(25), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    location = db.Column(db.String(100))
    bio = db.Column(db.Text)
    posts = db.relationship('Post', backref='author', lazy=True)
    gardens = db.relationship('Garden', secondary='user_garden', back_populates='members')

    def get_reset_token(self, expires_sec=1800):
        """Generate a token that expires after a set time (default: 30 minutes)."""
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'userId': self.id})

    @staticmethod
    def verify_reset_token(token):
        """Verify a reset token and return the corresponding user if valid."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=1800)  # Enforces expiration
        except (BadSignature, SignatureExpired):
            return None  # Invalid or expired token
        return User.query.get(data['userId'])

    def get_role_in_garden(self, garden_id):
        """Get the user's role in a specific garden."""
        result = db.session.query(user_garden.c.role).filter(
            user_garden.c.user_id == self.id,
            user_garden.c.garden_id == garden_id
        ).first()
        return result[0] if result else None

    def has_commercial_access(self, garden_id):
        """Check if user has commercial access in a garden."""
        role = self.get_role_in_garden(garden_id)
        return role in ('commercial', 'manager')

    def has_manager_access(self, garden_id):
        """Check if user has manager access in a garden."""
        role = self.get_role_in_garden(garden_id)
        return role == 'manager'

    def __repr__(self):
        return f"User({self.firstName} {self.lastName}, {self.email}, {self.image_file})"

class DynamicAttribute(db.Model):
    __tablename__ = 'dynamic_attribute'
    id = db.Column(db.Integer, primary_key=True)
    
    # Entity identification
    entity_type = db.Column(db.String(50), nullable=False)  # e.g., 'plant_detail', 'variety', 'zone', 'garden'
    entity_id = db.Column(db.Integer, nullable=False)
    
    # Attribute information
    name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)

    __table_args__ = (
        db.Index('idx_entity', 'entity_type', 'entity_id'),  # Index for faster lookups
    )

    def __repr__(self):
        return f"DynamicAttribute({self.entity_type}.{self.name}: {self.value})"

# Mixin to add dynamic attribute functionality to any model
class DynamicAttributeMixin:
    @property
    def entity_type(self):
        """Return the entity type for the dynamic attribute"""
        return self.__tablename__

    def set_attribute(self, name, value, category='default'):
        """Set a dynamic attribute"""
        attr = DynamicAttribute.query.filter_by(
            entity_type=self.entity_type,
            entity_id=self.id,
            name=name
        ).first()
        
        if attr:
            attr.value = value
            attr.category = category
        else:
            attr = DynamicAttribute(
                entity_type=self.entity_type,
                entity_id=self.id,
                name=name,
                value=value,
                category=category
            )
            db.session.add(attr)
        
        db.session.commit()

    def get_attribute(self, name):
        """Get a dynamic attribute value"""
        attr = DynamicAttribute.query.filter_by(
            entity_type=self.entity_type,
            entity_id=self.id,
            name=name
        ).first()
        return attr.value if attr else None

    def get_attributes_by_category(self, category):
        """Get all attributes in a category"""
        attrs = DynamicAttribute.query.filter_by(
            entity_type=self.entity_type,
            entity_id=self.id,
            category=category
        ).all()
        return {attr.name: attr.value for attr in attrs}

    def get_all_attributes(self):
        """Get all attributes grouped by category"""
        attrs = DynamicAttribute.query.filter_by(
            entity_type=self.entity_type,
            entity_id=self.id
        ).all()
        
        result = {}
        for attr in attrs:
            if attr.category not in result:
                result[attr.category] = {}
            result[attr.category][attr.name] = attr.value
        return result

class Garden(db.Model, DynamicAttributeMixin):
    __tablename__ = 'garden'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    garden_type = db.Column(db.String(50), nullable=True)
    garden_size = db.Column(db.Float, nullable=True)
    timezone = db.Column(db.String(50), nullable=True)

    # Relationships
    owner = db.relationship('User', foreign_keys=[owner_id], backref='owned_gardens')
    members = db.relationship('User', secondary='user_garden', back_populates='gardens')
    zones = db.relationship('Zone', backref='garden', lazy=True)
    posts = db.relationship('Post', backref='garden', lazy=True)

    def add_member(self, user, role='member'):
        """Add a member to the garden with a specific role."""
        if role not in ('member', 'commercial', 'manager'):
            raise ValueError("Invalid role. Must be 'member', 'commercial', or 'manager'")
        
        # Remove existing membership if it exists
        self.remove_member(user)
        
        # Add new membership with specified role
        stmt = user_garden.insert().values(
            user_id=user.id,
            garden_id=self.id,
            role=role
        )
        db.session.execute(stmt)
        db.session.commit()

    def remove_member(self, user):
        """Remove a member from the garden."""
        stmt = user_garden.delete().where(
            user_garden.c.user_id == user.id,
            user_garden.c.garden_id == self.id
        )
        db.session.execute(stmt)
        db.session.commit()

    def update_member_role(self, user, new_role):
        """Update a member's role in the garden."""
        if new_role not in ('member', 'commercial', 'manager'):
            raise ValueError("Invalid role. Must be 'member', 'commercial', or 'manager'")
        
        stmt = user_garden.update().where(
            user_garden.c.user_id == user.id,
            user_garden.c.garden_id == self.id
        ).values(role=new_role)
        db.session.execute(stmt)
        db.session.commit()

    def get_members_by_role(self, role):
        """Get all members with a specific role."""
        return User.query.join(user_garden).filter(
            user_garden.c.garden_id == self.id,
            user_garden.c.role == role
        ).all()

    def get_commercial_members(self):
        """Get all members with commercial access (commercial and manager roles)."""
        return User.query.join(user_garden).filter(
            user_garden.c.garden_id == self.id,
            user_garden.c.role.in_(['commercial', 'manager'])
        ).all()

    def get_member_role(self, user):
        """Get a member's role in the garden."""
        return user.get_role_in_garden(self.id)

    def __repr__(self):
        return f"Garden({self.name}, {self.location})"

class Zone(db.Model, DynamicAttributeMixin):
    __tablename__ = 'zone'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    garden_id = db.Column(db.Integer, db.ForeignKey('garden.id'), nullable=False)
    
    plants = db.relationship('Plant', backref='zone', lazy=True)

    def set_growing_condition(self, name, value):
        """Helper method to set growing conditions"""
        self.set_attribute(name, value, category='growing_conditions')

    def set_soil_info(self, name, value):
        """Helper method to set soil information"""
        self.set_attribute(name, value, category='soil_info')

    def get_growing_conditions(self):
        """Helper method to get all growing conditions"""
        return self.get_attributes_by_category('growing_conditions')

    def get_soil_info(self):
        """Helper method to get all soil information"""
        return self.get_attributes_by_category('soil_info')

    def __repr__(self):
        return f"Zone({self.name}, Garden ID: {self.garden_id})"

class PlantDetail(db.Model, DynamicAttributeMixin):
    __tablename__ = 'plant_detail'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    scientific_name = db.Column(db.String(100))
    category = db.Column(db.String(50))  # e.g., "Vegetable", "Herb", "Fruit"
    description = db.Column(db.Text)
    
    # Relationships
    attributes = db.relationship('PlantAttribute', backref='plant_detail', lazy=True,
                               cascade='all, delete-orphan')
    varieties = db.relationship('PlantVariety', backref='plant_detail', lazy=True)
    plants = db.relationship('Plant', backref='plant_detail', lazy=True)

    def set_attribute(self, name, value, category='growing_info'):
        """Set a plant attribute"""
        attr = PlantAttribute.query.filter_by(
            plant_detail_id=self.id,
            name=name
        ).first()
        
        if attr:
            attr.value = value
            attr.category = category
        else:
            attr = PlantAttribute(
                plant_detail_id=self.id,
                name=name,
                value=value,
                category=category
            )
            db.session.add(attr)
        
        db.session.commit()

    def get_attribute(self, name):
        """Get a plant attribute value"""
        attr = PlantAttribute.query.filter_by(
            plant_detail_id=self.id,
            name=name
        ).first()
        return attr.value if attr else None

    def get_attributes_by_category(self, category):
        """Get all attributes in a category"""
        return {attr.name: attr.value for attr in self.attributes 
                if attr.category == category}

    def __repr__(self):
        return f"PlantDetail({self.name}, {self.category})"

class PlantAttribute(db.Model):
    __tablename__ = 'plant_attribute'
    id = db.Column(db.Integer, primary_key=True)
    plant_detail_id = db.Column(db.Integer, db.ForeignKey('plant_detail.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # e.g., "days_to_maturity", "height"
    value = db.Column(db.String(100), nullable=False)  # Store all values as strings
    category = db.Column(db.String(50), nullable=False)  # e.g., "growing_info", "characteristics"

    def __repr__(self):
        return f"PlantAttribute({self.name}: {self.value})"

class VarietyAttribute(db.Model):
    __tablename__ = 'variety_attribute'
    id = db.Column(db.Integer, primary_key=True)
    variety_id = db.Column(db.Integer, db.ForeignKey('plant_variety.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # e.g., "days_to_maturity", "height"
    value = db.Column(db.String(100), nullable=False)  # Store all values as strings
    category = db.Column(db.String(50), nullable=False)  # e.g., "characteristics", "resistance"

    def __repr__(self):
        return f"VarietyAttribute({self.name}: {self.value})"

class PlantVariety(db.Model, DynamicAttributeMixin):
    __tablename__ = 'plant_variety'
    id = db.Column(db.Integer, primary_key=True)
    plant_detail_id = db.Column(db.Integer, db.ForeignKey('plant_detail.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    attributes = db.relationship('VarietyAttribute', backref='variety', lazy=True,
                               cascade='all, delete-orphan')
    plants = db.relationship('Plant', backref='variety', lazy=True)

    def set_attribute(self, name, value, category='characteristics'):
        """Set a variety attribute"""
        attr = VarietyAttribute.query.filter_by(
            variety_id=self.id,
            name=name
        ).first()
        
        if attr:
            attr.value = value
            attr.category = category
        else:
            attr = VarietyAttribute(
                variety_id=self.id,
                name=name,
                value=value,
                category=category
            )
            db.session.add(attr)
        
        db.session.commit()

    def get_attribute(self, name):
        """Get a variety attribute value"""
        attr = VarietyAttribute.query.filter_by(
            variety_id=self.id,
            name=name
        ).first()
        return attr.value if attr else None

    def get_attributes_by_category(self, category):
        """Get all attributes in a category"""
        return {attr.name: attr.value for attr in self.attributes 
                if attr.category == category}

    def __repr__(self):
        return f"PlantVariety({self.name}, Plant: {self.plant_detail.name})"

class PlantStatus(db.Model):
    __tablename__ = 'plant_status'
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Seedling')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"PlantStatus({self.status}, Updated: {self.created_at})"

class Plant(db.Model):
    __tablename__ = 'plant'
    id = db.Column(db.Integer, primary_key=True)
    plant_detail_id = db.Column(db.Integer, db.ForeignKey('plant_detail.id'), nullable=False)
    variety_id = db.Column(db.Integer, db.ForeignKey('plant_variety.id'), nullable=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    planting_date = db.Column(db.DateTime)
    
    # Use growth_stages instead of status_history
    growth_stages = db.relationship('PlantTracking', backref='plant', lazy=True,
                                  order_by='desc(PlantTracking.date_logged)')

    @property
    def status(self):
        """Get the current growth stage"""
        # Force a fresh query
        db.session.expire_all()
        latest_stage = PlantTracking.query.filter_by(plant_id=self.id)\
            .order_by(PlantTracking.date_logged.desc())\
            .first()
        if latest_stage:
            print(f"Found latest stage for plant {self.id}: {latest_stage.stage}")
            return latest_stage.stage
        print(f"No stage found for plant {self.id}, returning Seedling")
        return 'Seedling'

    def update_status(self, new_status, notes=None, image_file=None):
        """Update plant stage using PlantTracking"""
        tracking = PlantTracking(
            plant_id=self.id,
            stage=new_status,
            notes=notes,
            image_file=image_file,
            date_logged=datetime.utcnow()
        )
        db.session.add(tracking)
        db.session.commit()
        return tracking

    def set_initial_status(self, status='Seedling', notes=None):
        """Set the initial stage for a new plant"""
        if not self.id:
            db.session.flush()  # Ensure the plant has an ID
        tracking = PlantTracking(
            plant_id=self.id,
            stage=status,
            notes=notes,
            date_logged=self.planting_date or datetime.utcnow()
        )
        db.session.add(tracking)
        return tracking

    # Add fields for recurring harvests
    total_harvests = db.Column(db.Integer, default=0)
  
    # Relationships
    growth_stages = db.relationship('PlantTracking', backref='plant', lazy=True)
    harvests = db.relationship('Harvest', backref='plant', lazy=True)

    def schedule_next_harvest(self):
        """Calculate and set the next harvest date"""
        if self.is_recurring_harvest and self.harvest_frequency_days:
            last_harvest = max((h.date for h in self.harvests), default=self.planting_date)
            self.next_harvest_date = last_harvest + timedelta(days=self.harvest_frequency_days)
            return self.next_harvest_date
        return None

    def add_harvest(self, amount, notes=None):
        """Add a new harvest record"""
        harvest = Harvest(
            plant_id=self.id,
            amount_collected=amount,
            notes=notes,
            harvest_number=self.total_harvests + 1
        )
        self.total_harvests += 1
        
        if self.is_recurring_harvest:
            self.schedule_next_harvest()
        
        db.session.add(harvest)
        db.session.commit()
        return harvest

    def get_harvest_stats(self):
        """Get statistics about plant harvests"""
        total_amount = sum(h.amount_collected for h in self.harvests)
        avg_amount = total_amount / len(self.harvests) if self.harvests else 0
        return {
            'total_harvests': len(self.harvests),
            'total_amount': total_amount,
            'average_amount': avg_amount,
            'first_harvest': min(h.date for h in self.harvests) if self.harvests else None,
            'last_harvest': max(h.date for h in self.harvests) if self.harvests else None,
            'next_harvest': self.next_harvest_date if self.is_recurring_harvest else None
        }

    def __repr__(self):
        variety_name = self.variety.name if self.variety else "No variety"
        return f"Plant({self.plant_detail.name}, Variety: {variety_name})"

class PlantTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    date_logged = db.Column(db.DateTime, default=datetime.utcnow)
    
    stage = db.Column(db.String(50), nullable=False)  # e.g., "Seeded", "Sprouted", "Flowering", "Harvested"
    notes = db.Column(db.Text, nullable=True)  # Optional user notes
    image_file = db.Column(db.String(100), nullable=True)  # ✅ Store image filename

    def __repr__(self):
        return f"PlantTracking(Stage: {self.stage}, Date: {self.date_logged})"

class Harvest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)  # When the harvest started
    completed_date = db.Column(db.DateTime)  # When the harvest was completed
    amount_collected = db.Column(db.Float, nullable=False)  # Yield amount
    notes = db.Column(db.Text, nullable=True)
    harvest_number = db.Column(db.Integer)  # Which harvest this is for the plant

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.plant_id:
            plant = Plant.query.get(self.plant_id)
            plant.total_harvests += 1
            self.harvest_number = plant.total_harvests

    def __repr__(self):
        return f"Harvest(Date: {self.date}, Amount: {self.amount_collected})"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    read_time = db.Column(db.Integer, nullable=False, default=5)  # in minutes
    category = db.Column(db.String(50), nullable=False)  # e.g., 'Herbs', 'Vegetables', 'Flowers'
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    garden_id = db.Column(db.Integer, db.ForeignKey('garden.id'), nullable=True)

    # Garden Details
    garden_type = db.Column(db.String(50), nullable=True)  # e.g., 'Balcony Garden', 'Backyard Garden'
    garden_size = db.Column(db.Float, nullable=True)  # in square feet
    plant_count = db.Column(db.Integer, nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)

    # Growing Conditions
    sunlight = db.Column(db.String(50), nullable=True)  # e.g., 'Full Sun', 'Partial Shade'
    watering = db.Column(db.String(50), nullable=True)  # e.g., 'Daily Watering'
    zone = db.Column(db.String(20), nullable=True)  # e.g., 'Zone 6'

    # Relationships
    images = db.relationship('PostImage', backref='post', lazy=True, cascade='all, delete-orphan')
    plants = db.relationship('PostPlant', backref='post', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"Post({self.title}, {self.date_posted})"
    
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)

    orders = db.relationship('Order', backref='client', lazy=True)

    def __repr__(self):
        return f"Client({self.name}, {self.email})"

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    garden_id = db.Column(db.Integer, db.ForeignKey('garden.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_placed = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, completed, cancelled
    recurring = db.Column(db.Boolean, default=False)
    recurring_frequency = db.Column(db.String(20), nullable=True)  # weekly, monthly
    next_order_date = db.Column(db.DateTime, nullable=True)

    # Additional relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    delivery = db.relationship('Delivery', uselist=False, backref='order', lazy=True)
    payments = db.relationship('Payment', backref='order', lazy=True)
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_orders')
    garden = db.relationship('Garden', backref='orders')

    # Class-level constants
    VALID_STATUSES = ['pending', 'processing', 'completed', 'cancelled']
    VALID_FREQUENCIES = ['weekly', 'monthly']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not User.query.get(self.created_by).has_commercial_access(self.garden_id):
            raise ValueError("User does not have commercial access in this garden")
        
        # Validate status
        if 'status' in kwargs and kwargs['status'] not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
        
        # Validate recurring frequency
        if self.recurring and self.recurring_frequency not in self.VALID_FREQUENCIES:
            raise ValueError(f"Invalid recurring frequency. Must be one of: {', '.join(self.VALID_FREQUENCIES)}")

    def calculate_total(self):
        """Recalculate the total order amount based on order items."""
        self.total_amount = sum(item.quantity * item.price_per_unit for item in self.order_items)
        db.session.commit()

    def generate_next_order(self):
        """Create the next recurring order based on frequency."""
        if not self.recurring:
            return None

        if self.recurring_frequency == "weekly":
            next_date = self.date_placed + timedelta(weeks=1)
        elif self.recurring_frequency == "monthly":
            next_date = self.date_placed + timedelta(weeks=4)
        else:
            return None

        new_order = Order(
            client_id=self.client_id,
            garden_id=self.garden_id,
            created_by=self.created_by,
            total_amount=self.total_amount,
            recurring=True,
            recurring_frequency=self.recurring_frequency,
            next_order_date=next_date
        )

        # Copy order items
        for item in self.order_items:
            new_item = OrderItem(
                plant_id=item.plant_id,
                quantity=item.quantity,
                price_per_unit=item.price_per_unit
            )
            new_order.order_items.append(new_item)

        db.session.add(new_order)
        db.session.commit()
        return new_order

    def update_status(self, new_status):
        """Update order status with validation."""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
        self.status = new_status
        db.session.commit()

    def add_payment(self, amount, payment_method, status="pending"):
        """Add a new payment to the order."""
        payment = Payment(
            order_id=self.id,
            amount=amount,
            payment_method=payment_method,
            status=status
        )
        db.session.add(payment)
        db.session.commit()
        return payment

    def get_remaining_balance(self):
        """Calculate remaining balance based on payments."""
        paid_amount = sum(payment.amount for payment in self.payments if payment.status == "completed")
        return self.total_amount - paid_amount

    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        return self.status in ['pending', 'processing']

    @staticmethod
    def get_orders_for_user(user_id):
        """Get all orders created by a user in gardens where they have commercial access."""
        return Order.query.join(Garden).join(user_garden).filter(
            user_garden.c.user_id == user_id,
            user_garden.c.role.in_(['commercial', 'manager'])
        ).all()

    @staticmethod
    def get_orders_by_status(status):
        """Get all orders with a specific status."""
        if status not in Order.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(Order.VALID_STATUSES)}")
        return Order.query.filter_by(status=status).all()

    def __repr__(self):
        return f"Order(Client: {self.client.name}, Status: {self.status}, Total: {self.total_amount}, Recurring: {self.recurring})"
    
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=True)  # ✅ Supports multiple plants
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"OrderItem(Order: {self.order_id}, Plant: {self.plant_id}, Quantity: {self.quantity}, Price: {self.price_per_unit})"

class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    delivery_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default="Not Shipped")  # e.g., "Not Shipped", "In Transit", "Delivered"
    tracking_number = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=False)  # Add this line

    def __repr__(self):
        return f"Delivery(Order ID: {self.order_id}, Status: {self.status})"

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)  # e.g., "Credit Card", "PayPal", "Bank Transfer"
    status = db.Column(db.String(50), default="Pending")  # e.g., "Pending", "Completed", "Failed"

    def __repr__(self):
        return f"Payment(Order ID: {self.order_id}, Amount: {self.amount}, Status: {self.status})"

class PostImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    image_file = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(200), nullable=True)
    order = db.Column(db.Integer, nullable=False, default=0)  # For carousel order

class PostPlant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # e.g., 'Basil', 'Tomatoes'
    status = db.Column(db.String(20), nullable=False)  # e.g., 'Growing', 'Fruiting'
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=True)  # Optional link to actual plant
