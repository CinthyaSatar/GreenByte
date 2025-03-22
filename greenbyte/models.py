from datetime import datetime
from itsdangerous import Serializer, BadSignature, SignatureExpired
from greenbyte import db, login_manager
from flask_login import UserMixin
from flask import current_app

@login_manager.user_loader
def loadUser(userId):
    return User.query.get(int(userId))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstName  = db.Column(db.String(25), nullable=False )
    lastName  = db.Column(db.String(25), nullable=False )
    email  = db.Column(db.String(120), unique=True, nullable=False )
    image_file = db.Column(db.String(25),  nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True )
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

    def __repr__(self):
        return f"User({self.firstName} {self.lastName}, {self.email}, {self.image_file})"

# Many-to-Many Relationship for Users and Gardens
user_garden = db.Table('user_garden',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('garden_id', db.Integer, db.ForeignKey('garden.id'), primary_key=True)
)

class Garden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(200), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    members = db.relationship('User', secondary=user_garden, back_populates='gardens')
    grow_spaces = db.relationship('GrowSpace', backref='garden', lazy=True)

    def __repr__(self):
        return f"Garden({self.name}, {self.location})"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    datePosted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    grow_space_id = db.Column(db.Integer, db.ForeignKey('grow_space.id'), nullable=True)

    grow_space = db.relationship('GrowSpace', backref='posts')

    def __repr__(self):
        return f"Post({self.title} {self.datePosted})"

class GrowSpace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    garden_id = db.Column(db.Integer, db.ForeignKey('garden.id'), nullable=False)
    section = db.Column(db.String(50), nullable=True)
    planting_date = db.Column(db.DateTime, nullable=True)
    plants = db.relationship('Plant', backref='grow_space', lazy=True)

    def __repr__(self):
        return f"GrowSpace({self.name}, Section {self.section})"
    
class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    planting_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    grow_space_id = db.Column(db.Integer, db.ForeignKey('grow_space.id'), nullable=False)

    def __repr__(self):
        return f"Plant({self.name}, Planted on {self.planting_date})"
