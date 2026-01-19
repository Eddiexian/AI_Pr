from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import json

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False) # In real app, hash this!
    role = db.Column(db.String(20), nullable=False, default='worker') # worker, maintainer, admin
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role
        }

class Layout(db.Model):
    __tablename__ = 'layouts'
    
    id = db.Column(db.String(36), primary_key=True) # UUID
    name = db.Column(db.String(100), nullable=False)
    width = db.Column(db.Integer, default=800)
    height = db.Column(db.Integer, default=600)
    # Metadata for grouping (e.g., Floor 6, Test Area)
    floor = db.Column(db.String(20))
    area = db.Column(db.String(50))
    
    components = db.relationship('Component', backref='layout', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'floor': self.floor,
            'area': self.area
        }

class Component(db.Model):
    __tablename__ = 'components'
    
    id = db.Column(db.String(36), primary_key=True) # UUID
    layout_id = db.Column(db.String(36), db.ForeignKey('layouts.id'), nullable=False)
    
    type = db.Column(db.String(20), nullable=False) # bin, pillar, marker
    
    # Coordinates/Dimensions for Rectangular items (Successor to x, y, w, h)
    # But for Polygons, we use shape_date
    x = db.Column(db.Float, default=0)
    y = db.Column(db.Float, default=0)
    width = db.Column(db.Float, default=100)
    height = db.Column(db.Float, default=100)
    rotation = db.Column(db.Float, default=0)
    
    # For Non-rectangular shapes (Polygon)
    # Stored as JSON string: [{"x":0, "y":0}, {"x":10, "y":0}, ...]
    shape_points = db.Column(db.Text, nullable=True) 
    
    # Business Data
    code = db.Column(db.String(50)) # Bin Code e.g., A-01-01
    
    # Props (Color, Style, etc.) stored as JSON
    props = db.Column(db.Text, default='{}')

    def to_dict(self):
        return {
            'id': self.id,
            'layoutId': self.layout_id,
            'type': self.type,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'rotation': self.rotation,
            'shapePoints': json.loads(self.shape_points) if self.shape_points else None,
            'code': self.code,
            'props': json.loads(self.props) if self.props else {}
        }
