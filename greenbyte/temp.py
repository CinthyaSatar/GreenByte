from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.ext.associationproxy import association_proxy

db = SQLAlchemy()

VALID_GARDEN_ROLES = ["member", "commercial", "manager"]

# Association table definition
user_garden = db.Table('user_garden',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('garden_id', db.Integer, db.ForeignKey('garden.id'), primary_key=True),
    db.Column('role', db.String(50), nullable=False, default="member")
)

class User(db.Model, UserMixin):
    __tablename__ = 'user'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    firstName = db.Column(db.String(25), nullable=False)
    lastName = db.Column(db.String(25), nullable=False)
    image_file = db.Column(db.String(25), nullable=False, default='default.jpg')
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    gardens = db.relationship('Garden', secondary=user_garden, back_populates='members')
    posts = db.relationship('Post', backref='author', lazy=True)
    
    garden_roles = association_proxy('gardens', 'role')

    def get_role_in_garden(self, garden_id):
        """Return the user's role in a specific garden."""
        garden_membership = db.session.query(user_garden).filter_by(
            user_id=self.id, 
            garden_id=garden_id
        ).first()
        return garden_membership.role if garden_membership else None

    def __repr__(self):
        return f"User({self.username}, {self.email})"

class Garden(db.Model):
    __tablename__ = 'garden'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    members = db.relationship('User', secondary=user_garden, back_populates='gardens')
    zones = db.relationship('Zone', backref='garden', lazy=True)
    posts = db.relationship('Post', backref='garden', lazy=True)
    
    member_roles = association_proxy('members', 'role')

    @staticmethod
    def validate_role(role):
        """Validate that a role is acceptable."""
        if role not in VALID_GARDEN_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(VALID_GARDEN_ROLES)}")
        return role

    def add_member(self, user, role="member"):
        """Add a member to the garden with a specific role."""
        self.validate_role(role)
        if user not in self.members:
            self.members.append(user)
            db.session.flush()  # Ensure IDs are generated
            self.set_member_role(user.id, role)

    def set_member_role(self, user_id, role):
        """Set the role of a member in the garden."""
        self.validate_role(role)
        db.session.execute(
            user_garden.update()
            .where(user_garden.c.user_id == user_id)
            .where(user_garden.c.garden_id == self.id)
            .values(role=role)
        )

    def get_commercial_members(self):
        """Return members with the 'commercial' role."""
        return [
            member for member, role in 
            db.session.query(User, user_garden.c.role)
            .join(user_garden)
            .filter(user_garden.c.garden_id == self.id)
            .filter(user_garden.c.role == "commercial")
            .all()
        ]

    def __repr__(self):
        return f"Garden({self.name}, {self.location})"

class Zone(db.Model):
    __tablename__ = 'zone'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    garden_id = db.Column(db.Integer, db.ForeignKey('garden.id'), nullable=False)

    plants = db.relationship('Plant', backref='zone', lazy=True)

    def __repr__(self):
        return f"Zone({self.name}, Garden ID: {self.garden_id})"

class Plant(db.Model):
    __tablename__ = 'plant'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False)
    planting_date = db.Column(db.DateTime, default=datetime.utcnow)

    growth_stages = db.relationship('PlantTracking', backref='plant', lazy=True)
    harvests = db.relationship('Harvest', backref='plant', lazy=True)  # ✅ Multiple harvests per plant

class PlantTracking(db.Model):
    __tablename__ = 'plant_tracking'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    date_logged = db.Column(db.DateTime, default=datetime.utcnow)
    
    stage = db.Column(db.String(50), nullable=False)  # e.g., "Seeded", "Sprouted", "Flowering", "Harvested"
    notes = db.Column(db.Text, nullable=True)  # Optional user notes
    image_file = db.Column(db.String(100), nullable=True)  # ✅ Store image filename

    def __repr__(self):
        return f"PlantTracking(Stage: {self.stage}, Date: {self.date_logged})"
    
class Harvest(db.Model):
    __tablename__ = 'harvest'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)  # When the harvest occurred
    amount_collected = db.Column(db.Float, nullable=False)  # Yield amount (weight, count, etc.)
    notes = db.Column(db.Text, nullable=True)  # Optional harvest notes

    def __repr__(self):
        return f"Harvest(Date: {self.date}, Amount: {self.amount_collected})"

class Post(db.Model):
    __tablename__ = 'post'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    garden_id = db.Column(db.Integer, db.ForeignKey('garden.id'), nullable=True)  # Link posts to gardens

    def __repr__(self):
        return f"Post({self.title}, {self.date_posted})"
    

class Client(db.Model):
    __tablename__ = 'client'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)

    orders = db.relationship('Order', backref='client', lazy=True)

    def __repr__(self):
        return f"Client({self.name}, {self.email})"

class Order(db.Model):
    __tablename__ = 'order'  # Explicitly define table name
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    date_placed = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pending")  # e.g., "Pending", "Completed", "Cancelled"

    recurring = db.Column(db.Boolean, default=False)  # ✅ True if this is a recurring order
    recurring_frequency = db.Column(db.String(20), nullable=True)  # e.g., "weekly", "monthly"
    next_order_date = db.Column(db.DateTime, nullable=True)  # Auto-set for recurring orders

    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    delivery = db.relationship('Delivery', uselist=False, backref='order')

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
            return None  # Invalid frequency

        new_order = Order(
            client_id=self.client_id,
            date_placed=next_date,
            total_amount=self.total_amount,
            status="Pending",
            recurring=True,
            recurring_frequency=self.recurring_frequency,
            next_order_date=next_date
        )
        db.session.add(new_order)
        db.session.commit()

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
