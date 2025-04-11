from datetime import datetime, timedelta
from enum import Enum
from itsdangerous import Serializer, BadSignature, SignatureExpired
from greenbyte import db, login_manager
from flask_login import UserMixin
from flask import current_app
from sqlalchemy_utils import TimezoneType
from sqlalchemy.ext.hybrid import hybrid_property
from .utils.timezone import now_in_timezone, get_current_timezone


class PlantStage(str, Enum):
    """Enum for plant stages/statuses"""
    SEEDLING = 'Seedling'
    GROWING = 'Growing'
    MATURE = 'Mature'
    HARVESTING = 'Harvesting'
    DORMANT = 'Dormant'
    FLOWERING = 'Flowering'
    FRUITING = 'Fruiting'
    TRANSPLANTED = 'Transplanted'
    DISEASED = 'Diseased'
    COMPLETED = 'Completed'

    @classmethod
    def list(cls):
        """Return a list of all status values"""
        return [e.value for e in cls]

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Many-to-Many Relationship for Users and Gardens
user_garden = db.Table('user_garden',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('garden_id', db.Integer, db.ForeignKey('garden.id'), primary_key=True),
    db.Column('role', db.String(20), nullable=False, default='member')  # 'member', 'commercial', 'manager'
)

# Many-to-Many Relationship for Farms and Users
farm_member = db.Table('farm_member',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('farm_id', db.Integer, db.ForeignKey('farm.id'), primary_key=True),
    db.Column('role', db.String(20), nullable=False, default='gardener')  # 'admin', 'gardener'
)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    firstName = db.Column(db.String(25), nullable=False)
    lastName = db.Column(db.String(25), nullable=False)
    image_file = db.Column(db.String(25), nullable=False, default='default.jpg')
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    access_level = db.Column(db.String(20), nullable=False, default='user')  # 'user', 'admin', 'superadmin'

    # Define the relationship with gardens using back_populates
    gardens = db.relationship('Garden', secondary=user_garden, back_populates='members')
    posts = db.relationship('Post', backref='author', lazy=True)

    # Farm relationships
    farms = db.relationship('Farm', secondary=farm_member, backref='members')

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

    def is_super_user(self):
        """Check if user is a super user who can create farms."""
        # This could be based on a field in the user model, or a specific role
        # For now, we'll consider users with 'admin' or 'superadmin' access level as super users
        try:
            return self.access_level in ['admin', 'superadmin']
        except AttributeError:
            # If access_level is not set, default to False
            return False

    def get_farm_role(self, farm_id):
        """Get the user's role in a specific farm."""
        result = db.session.query(farm_member.c.role).filter(
            farm_member.c.user_id == self.id,
            farm_member.c.farm_id == farm_id
        ).first()
        return result[0] if result else None

    def is_farm_admin(self, farm_id):
        """Check if user has admin role in a farm."""
        return self.get_farm_role(farm_id) == 'admin'

    def is_farm_gardener(self, farm_id):
        """Check if user has gardener role in a farm."""
        return self.get_farm_role(farm_id) == 'gardener'

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
            name=name,
            category=category
        ).first()

        if attr:
            attr.value = value
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

    def get_attribute(self, name, category='default'):
        """Get a dynamic attribute value"""
        attr = DynamicAttribute.query.filter_by(
            entity_type=self.entity_type,
            entity_id=self.id,
            name=name,
            category=category
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
    __tablename__ = 'garden'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_updated = db.Column(db.DateTime, default=now_in_timezone)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=True)  # Optional link to a farm

    # Add owner relationship
    owner = db.relationship('User', foreign_keys=[owner_id], backref='owned_gardens')

    # Existing relationships
    members = db.relationship('User', secondary=user_garden, back_populates='gardens')
    zones = db.relationship('Zone', backref='garden', lazy=True)

    def get_plant_statuses(self):
        """Get a combined list of all unique plant statuses across all zones"""
        all_statuses = set()
        for zone in self.zones:
            all_statuses.update(zone.get_plant_statuses())
        return sorted(list(all_statuses))

    def set_plant_statuses(self, statuses):
        """Set the available plant statuses for all zones in this garden"""
        for zone in self.zones:
            zone.set_plant_statuses(statuses)

    def add_plant_status(self, status):
        """Add a new plant status to all zones in this garden"""
        for zone in self.zones:
            zone.add_plant_status(status)

    def remove_plant_status(self, status):
        """Remove a plant status from all zones in this garden"""
        for zone in self.zones:
            zone.remove_plant_status(status)

    def __repr__(self):
        return f"Garden({self.name})"

class Zone(db.Model, DynamicAttributeMixin):
    __tablename__ = 'zone'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    garden_id = db.Column(db.Integer, db.ForeignKey('garden.id'), nullable=False)

    plants = db.relationship('Plant', backref='zone', lazy=True)

    def set_plant_statuses(self, statuses):
        """Set the available plant statuses for this zone"""
        if not statuses:
            raise ValueError("At least one status is required")
        status_string = ','.join(statuses)
        print(f"Setting statuses for zone {self.id}: {status_string}")  # Debug print
        self.set_attribute('plant_statuses', status_string, category='plant_tracking')

    def get_plant_statuses(self):
        """Get the list of available plant statuses"""
        default_statuses = ['Seedling', 'Growing', 'Mature', 'Harvesting']
        stored_statuses = self.get_attribute('plant_statuses', category='plant_tracking')
        if stored_statuses:
            return stored_statuses.split(',')
        return default_statuses

    def add_plant_status(self, status):
        """Add a new plant status to the existing list"""
        current_statuses = self.get_plant_statuses()
        if status not in current_statuses:
            current_statuses.append(status)
            self.set_plant_statuses(current_statuses)

    def remove_plant_status(self, status):
        """Remove a plant status from the list"""
        current_statuses = self.get_plant_statuses()
        if status in current_statuses:
            current_statuses.remove(status)
            if current_statuses:  # Ensure we still have at least one status
                self.set_plant_statuses(current_statuses)

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
    created_at = db.Column(db.DateTime, default=now_in_timezone)
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
            return latest_stage.stage
        return 'Seedling'

    def update_status(self, new_status: str, notes: str = None, image_file: str = None) -> 'PlantTracking':
        """Update plant stage using PlantTracking

        Args:
            new_status (str): The new status/stage of the plant
            notes (str, optional): Additional notes about the status change
            image_file (str, optional): Path to an image file documenting the status

        Returns:
            PlantTracking: The newly created tracking record

        Raises:
            ValueError: If the status is not valid
        """
        # Validate the status
        if new_status not in PlantStage.list():
            raise ValueError(f"Invalid status: {new_status}. Must be one of {PlantStage.list()}")

        tracking = PlantTracking(
            plant_id=self.id,
            stage=new_status,
            notes=notes,
            image_file=image_file,
            date_logged=now_in_timezone()
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
            date_logged=self.planting_date or now_in_timezone()
        )
        db.session.add(tracking)
        return tracking

    # Add fields for recurring harvests
    total_harvests = db.Column(db.Integer, default=0)

    # Relationships
    growth_stages = db.relationship('PlantTracking', backref='plant', lazy=True,
                                  cascade='all, delete-orphan')
    harvests = db.relationship('Harvest', backref='plant', lazy=True,
                              cascade='all, delete-orphan')

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

    @hybrid_property
    def days_since_planting(self):
        """Get the number of days since the plant was planted

        Returns:
            int or None: Number of days since planting, or None if planting_date is not set
        """
        if not self.planting_date:
            return None
        return (now_in_timezone().date() - self.planting_date.date()).days

    def get_last_update_time(self) -> str:
        """Get the last update time in a human-readable format

        Returns:
            str: A human-readable string representing the time since the last update
        """
        latest_tracking = PlantTracking.query.filter_by(plant_id=self.id)\
            .order_by(PlantTracking.date_logged.desc())\
            .first()

        if not latest_tracking:
            return "Never updated"

        now = now_in_timezone()

        # Make sure the date_logged has timezone info
        date_logged = latest_tracking.date_logged
        if date_logged.tzinfo is None:
            # Convert naive datetime to aware datetime using the same timezone as now
            date_logged = date_logged.replace(tzinfo=now.tzinfo)

        diff = now - date_logged

        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                minutes = diff.seconds // 60
                if minutes == 0:
                    return "Just now"
                elif minutes == 1:
                    return "1 minute ago"
                else:
                    return f"{minutes} minutes ago"
            elif hours == 1:
                return "1 hour ago"
            else:
                return f"{hours} hours ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            if weeks == 1:
                return "1 week ago"
            else:
                return f"{weeks} weeks ago"
        elif diff.days < 365:
            months = diff.days // 30
            if months == 1:
                return "1 month ago"
            else:
                return f"{months} months ago"
        else:
            years = diff.days // 365
            if years == 1:
                return "1 year ago"
            else:
                return f"{years} years ago"

    def get_harvest_stats(self):
        """Get statistics about plant harvests

        Returns:
            dict: A dictionary containing:
                - total_harvests (int): The number of harvests
                - total_amount (float): The total amount collected across all harvests
                - average_amount (float): The average amount per harvest
                - first_harvest (datetime): The date of the first harvest, or None if no harvests
                - last_harvest (datetime): The date of the most recent harvest, or None if no harvests
                - next_harvest (datetime): The date of the next scheduled harvest, or None if not recurring
        """
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
    date_logged = db.Column(db.DateTime, default=now_in_timezone)

    stage = db.Column(db.String(50), nullable=False)  # e.g., "Seeded", "Sprouted", "Flowering", "Harvested"
    notes = db.Column(db.Text, nullable=True)  # Optional user notes
    image_file = db.Column(db.String(100), nullable=True)  # ✅ Store image filename

    # Add indexes for better performance
    __table_args__ = (
        db.Index('idx_plant_tracking_plant', 'plant_id'),
        db.Index('idx_plant_tracking_date', 'date_logged'),
    )

    def __repr__(self):
        return f"PlantTracking(Stage: {self.stage}, Date: {self.date_logged})"

class Harvest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    date = db.Column(db.DateTime, default=now_in_timezone)  # When the harvest started
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


# Many-to-Many Relationship for Posts and Tags
post_tag = db.Table('post_tag',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# Many-to-Many Relationship for Post Likes
post_like = db.Table('post_like',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=now_in_timezone)
)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    # Relationship with posts
    posts = db.relationship('Post', secondary=post_tag, back_populates='tags')

    def __repr__(self):
        return f"Tag('{self.name}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=now_in_timezone)
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
    garden = db.relationship('Garden', backref='posts', lazy=True)
    tags = db.relationship('Tag', secondary=post_tag, back_populates='posts', lazy=True)
    likes = db.relationship('User', secondary=post_like, backref=db.backref('liked_posts', lazy='dynamic'), lazy='dynamic')
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"Post({self.title}, {self.date_posted})"

    def like(self, user):
        """Add a like to the post"""
        if not self.is_liked_by(user):
            self.likes.append(user)
            return True
        return False

    def unlike(self, user):
        """Remove a like from the post"""
        if self.is_liked_by(user):
            self.likes.remove(user)
            return True
        return False

    def is_liked_by(self, user):
        """Check if the post is liked by a user"""
        return self.likes.filter(post_like.c.user_id == user.id).count() > 0

    @property
    def like_count(self):
        """Get the number of likes for the post"""
        return self.likes.count()

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=now_in_timezone)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)

    # Relationships
    author = db.relationship('User', backref='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __repr__(self):
        return f"Comment('{self.content[:20]}...', {self.date_posted})"


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
    date_placed = db.Column(db.DateTime, default=now_in_timezone)
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
    payment_date = db.Column(db.DateTime, default=now_in_timezone)
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

class EventType(db.Model):
    __tablename__ = 'event_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_default = db.Column(db.Boolean, default=False)  # True for system default types

    # Relationship with User
    user = db.relationship('User', backref=db.backref('event_types', lazy=True))

    def __repr__(self):
        return f"EventType('{self.name}', '{self.color}')"

    def to_dict(self):
        """Convert event type to dictionary for JSON response"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'is_default': self.is_default
        }

class CalendarEvent(db.Model):
    __tablename__ = 'calendar_event'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=True)
    all_day = db.Column(db.Boolean, default=False)
    repeat_type = db.Column(db.String(20), nullable=True)  # 'daily', 'weekly', 'monthly', 'yearly'
    repeat_end_date = db.Column(db.DateTime, nullable=True)
    calendar_type = db.Column(db.String(20), default='work')  # 'work', 'community', 'school', 'personal', 'todo', 'custom'
    event_type_id = db.Column(db.Integer, db.ForeignKey('event_type.id'), nullable=True)  # For custom event types
    url = db.Column(db.String(255), nullable=True)
    is_private = db.Column(db.Boolean, default=False)
    alert_before_minutes = db.Column(db.Integer, nullable=True)
    completed = db.Column(db.Boolean, default=False)  # Track completion status for TODO tasks
    completed_at = db.Column(db.DateTime, nullable=True)  # When the task was completed
    created_at = db.Column(db.DateTime, default=now_in_timezone)
    updated_at = db.Column(db.DateTime, default=now_in_timezone, onupdate=now_in_timezone)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    garden_id = db.Column(db.Integer, db.ForeignKey('garden.id'), nullable=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=True)

    # Relationships
    user = db.relationship('User', backref='calendar_events')
    garden = db.relationship('Garden', backref='calendar_events')
    zone = db.relationship('Zone', backref='calendar_events')
    plant = db.relationship('Plant', backref='calendar_events')
    event_type = db.relationship('EventType', backref='events')
    invitees = db.relationship('CalendarEventInvitee', backref='event', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"CalendarEvent({self.title}, {self.start_datetime})"

    def to_dict(self):
        """Convert event to dictionary for JSON response"""
        event_dict = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'start_datetime': self.start_datetime.isoformat() if self.start_datetime else None,
            'end_datetime': self.end_datetime.isoformat() if self.end_datetime else None,
            'all_day': self.all_day,
            'repeat_type': self.repeat_type,
            'repeat_end_date': self.repeat_end_date.isoformat() if self.repeat_end_date else None,
            'calendar_type': self.calendar_type,
            'url': self.url,
            'is_private': self.is_private,
            'alert_before_minutes': self.alert_before_minutes,
            'user_id': self.user_id,
            'garden_id': self.garden_id,
            'zone_id': self.zone_id,
            'plant_id': self.plant_id,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'garden': {'id': self.garden.id, 'name': self.garden.name} if self.garden else None,
            'zone': {'id': self.zone.id, 'name': self.zone.name} if self.zone else None,
            'plant': {'id': self.plant.id, 'name': self.plant.plant_detail.name} if self.plant else None
        }

        # Add event_type information if available
        if self.event_type_id and self.event_type:
            event_dict['event_type'] = self.event_type.to_dict()

        return event_dict

class CalendarEventInvitee(db.Model):
    __tablename__ = 'calendar_event_invitee'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('calendar_event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Can be null for external invitees
    email = db.Column(db.String(120), nullable=True)  # For external invitees
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'declined'

    # Relationship
    user = db.relationship('User', backref='event_invitations')

    def __repr__(self):
        return f"CalendarEventInvitee(Event: {self.event_id}, User: {self.user_id if self.user_id else self.email})"




class Farm(db.Model, DynamicAttributeMixin):
    """Farm model for commercial operations"""
    __tablename__ = 'farm'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=now_in_timezone)
    last_updated = db.Column(db.DateTime, default=now_in_timezone, onupdate=now_in_timezone)

    # Business information
    business_name = db.Column(db.String(100), nullable=True)
    tax_id = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(120), nullable=True)

    # Owner information
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', foreign_keys=[owner_id], backref='owned_farms')

    # Relationships
    gardens = db.relationship('Garden', backref='farm', lazy=True)
    inventory_items = db.relationship('InventoryItem', backref='farm', lazy=True)
    sales = db.relationship('Sale', backref='farm', lazy=True)

    def __repr__(self):
        return f"Farm({self.name}, {self.business_name or 'No business name'})"

    def get_member_role(self, user_id):
        """Get the user's role in this farm."""
        try:
            result = db.session.query(farm_member.c.role).filter(
                farm_member.c.user_id == user_id,
                farm_member.c.farm_id == self.id
            ).first()
            return result[0] if result else None
        except Exception:
            # If there's any error (e.g., table doesn't exist yet), return None
            return None

    def is_admin(self, user_id):
        """Check if user has admin role in this farm."""
        return self.get_member_role(user_id) == 'admin'

    def is_gardener(self, user_id):
        """Check if user has gardener role in this farm."""
        return self.get_member_role(user_id) == 'gardener'

    def add_member(self, user, role='gardener'):
        """Add a member to the farm with a specific role."""
        if role not in ['admin', 'gardener']:
            raise ValueError(f"Invalid role: {role}. Must be 'admin' or 'gardener'.")

        # Check if user is already a member
        existing_role = self.get_member_role(user.id)
        if existing_role:
            # Update role if different
            if existing_role != role:
                db.session.execute(
                    farm_member.update()
                    .where(farm_member.c.user_id == user.id)
                    .where(farm_member.c.farm_id == self.id)
                    .values(role=role)
                )
                db.session.commit()
            return False  # User was already a member

        # Add new member
        db.session.execute(
            farm_member.insert().values(
                user_id=user.id,
                farm_id=self.id,
                role=role
            )
        )
        db.session.commit()
        return True  # New member added

    def remove_member(self, user):
        """Remove a member from the farm."""
        if not self.get_member_role(user.id):
            return False  # User was not a member

        db.session.execute(
            farm_member.delete()
            .where(farm_member.c.user_id == user.id)
            .where(farm_member.c.farm_id == self.id)
        )
        db.session.commit()
        return True  # Member removed

    def get_admins(self):
        """Get all admin members of the farm."""
        return [
            member for member in
            db.session.query(User)
            .join(farm_member)
            .filter(farm_member.c.farm_id == self.id)
            .filter(farm_member.c.role == "admin")
            .all()
        ]

    def get_gardeners(self):
        """Get all gardener members of the farm."""
        return [
            member for member in
            db.session.query(User)
            .join(farm_member)
            .filter(farm_member.c.farm_id == self.id)
            .filter(farm_member.c.role == "gardener")
            .all()
        ]

class InventoryItem(db.Model):
    """Inventory item for a farm"""
    __tablename__ = 'inventory_item'
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)  # e.g., 'Produce', 'Seeds', 'Equipment'
    sku = db.Column(db.String(50), nullable=True)  # Stock Keeping Unit
    quantity = db.Column(db.Float, nullable=False, default=0)
    unit = db.Column(db.String(20), nullable=False, default='unit')  # e.g., 'kg', 'lb', 'unit'
    price_per_unit = db.Column(db.Float, nullable=True)
    cost_per_unit = db.Column(db.Float, nullable=True)
    reorder_point = db.Column(db.Float, nullable=True)  # When to reorder
    reorder_quantity = db.Column(db.Float, nullable=True)  # How much to reorder
    location = db.Column(db.String(100), nullable=True)  # Storage location
    created_at = db.Column(db.DateTime, default=now_in_timezone)
    last_updated = db.Column(db.DateTime, default=now_in_timezone, onupdate=now_in_timezone)

    # Optional link to a plant or harvest
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=True)
    harvest_id = db.Column(db.Integer, db.ForeignKey('harvest.id'), nullable=True)

    # Relationships
    plant = db.relationship('Plant', backref='inventory_items')
    harvest = db.relationship('Harvest', backref='inventory_items')
    inventory_transactions = db.relationship('InventoryTransaction', backref='item', lazy=True)

    def __repr__(self):
        return f"InventoryItem({self.name}, Qty: {self.quantity} {self.unit}, Farm: {self.farm_id})"

    def adjust_quantity(self, amount, reason=None, transaction_type='adjustment'):
        """Adjust the inventory quantity and create a transaction record."""
        old_quantity = self.quantity
        self.quantity += amount

        # Create transaction record
        transaction = InventoryTransaction(
            item_id=self.id,
            transaction_type=transaction_type,
            quantity_change=amount,
            previous_quantity=old_quantity,
            new_quantity=self.quantity,
            notes=reason
        )

        db.session.add(transaction)
        db.session.commit()
        return transaction

    def is_low_stock(self):
        """Check if item is below reorder point."""
        if self.reorder_point is None:
            return False
        return self.quantity <= self.reorder_point

class InventoryTransaction(db.Model):
    """Record of inventory changes"""
    __tablename__ = 'inventory_transaction'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # 'purchase', 'sale', 'adjustment', 'harvest', 'loss'
    quantity_change = db.Column(db.Float, nullable=False)  # Positive for additions, negative for reductions
    previous_quantity = db.Column(db.Float, nullable=False)
    new_quantity = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, default=now_in_timezone)
    notes = db.Column(db.Text, nullable=True)

    # Optional links to related records
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=True)

    def __repr__(self):
        return f"InventoryTransaction({self.transaction_type}, Change: {self.quantity_change}, Item: {self.item_id})"

class Sale(db.Model):
    """Sales record for a farm"""
    __tablename__ = 'sale'
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)  # Optional link to a client
    customer_name = db.Column(db.String(100), nullable=True)  # For one-time customers
    sale_date = db.Column(db.DateTime, default=now_in_timezone)
    total_amount = db.Column(db.Float, nullable=False, default=0)
    payment_method = db.Column(db.String(50), nullable=True)  # e.g., 'Cash', 'Credit Card', 'Check'
    payment_status = db.Column(db.String(50), default='pending')  # 'pending', 'completed', 'refunded'
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    customer = db.relationship('Client', backref='sales')
    creator = db.relationship('User', backref='created_sales')
    sale_items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    inventory_transactions = db.relationship('InventoryTransaction', backref='sale', lazy=True)

    def __repr__(self):
        return f"Sale(Date: {self.sale_date}, Amount: {self.total_amount}, Farm: {self.farm_id})"

    def calculate_total(self):
        """Calculate the total sale amount based on sale items."""
        self.total_amount = sum(item.quantity * item.price_per_unit for item in self.sale_items)
        db.session.commit()
        return self.total_amount

    def add_item(self, inventory_item, quantity, price_per_unit=None):
        """Add an item to the sale and update inventory."""
        # Use the inventory item's price if not specified
        if price_per_unit is None:
            price_per_unit = inventory_item.price_per_unit

        if price_per_unit is None:
            raise ValueError("Price per unit must be specified or available in the inventory item")

        # Check if there's enough inventory
        if inventory_item.quantity < quantity:
            raise ValueError(f"Not enough inventory. Available: {inventory_item.quantity} {inventory_item.unit}")

        # Create sale item
        sale_item = SaleItem(
            sale_id=self.id,
            inventory_item_id=inventory_item.id,
            quantity=quantity,
            price_per_unit=price_per_unit,
            total_price=quantity * price_per_unit
        )

        # Update inventory
        inventory_item.adjust_quantity(-quantity, f"Sale #{self.id}", 'sale')

        # Add sale item and update total
        db.session.add(sale_item)
        self.calculate_total()

        return sale_item

class SaleItem(db.Model):
    """Individual item in a sale"""
    __tablename__ = 'sale_item'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)  # quantity * price_per_unit

    # Relationship
    inventory_item = db.relationship('InventoryItem', backref='sale_items')

    def __repr__(self):
        return f"SaleItem(Item: {self.inventory_item_id}, Qty: {self.quantity}, Price: {self.price_per_unit})"

class Purchase(db.Model):
    """Purchase record for farm supplies/inventory"""
    __tablename__ = 'purchase'
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    supplier_name = db.Column(db.String(100), nullable=False)
    purchase_date = db.Column(db.DateTime, default=now_in_timezone)
    total_amount = db.Column(db.Float, nullable=False, default=0)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_status = db.Column(db.String(50), default='pending')  # 'pending', 'completed', 'refunded'
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    creator = db.relationship('User', backref='created_purchases')
    purchase_items = db.relationship('PurchaseItem', backref='purchase', lazy=True, cascade='all, delete-orphan')
    inventory_transactions = db.relationship('InventoryTransaction', backref='purchase', lazy=True)

    def __repr__(self):
        return f"Purchase(Date: {self.purchase_date}, Amount: {self.total_amount}, Farm: {self.farm_id})"

    def calculate_total(self):
        """Calculate the total purchase amount based on purchase items."""
        self.total_amount = sum(item.quantity * item.price_per_unit for item in self.purchase_items)
        db.session.commit()
        return self.total_amount

    def add_item(self, inventory_item, quantity, price_per_unit):
        """Add an item to the purchase and update inventory."""
        # Create purchase item
        purchase_item = PurchaseItem(
            purchase_id=self.id,
            inventory_item_id=inventory_item.id,
            quantity=quantity,
            price_per_unit=price_per_unit,
            total_price=quantity * price_per_unit
        )

        # Update inventory
        inventory_item.adjust_quantity(quantity, f"Purchase #{self.id}", 'purchase')

        # Add purchase item and update total
        db.session.add(purchase_item)
        self.calculate_total()

        return purchase_item

class PurchaseItem(db.Model):
    """Individual item in a purchase"""
    __tablename__ = 'purchase_item'
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)  # quantity * price_per_unit

    # Relationship
    inventory_item = db.relationship('InventoryItem', backref='purchase_items')

    def __repr__(self):
        return f"PurchaseItem(Item: {self.inventory_item_id}, Qty: {self.quantity}, Price: {self.price_per_unit})"
