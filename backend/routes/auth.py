from flask import Blueprint, request, jsonify
from models import db, User
from utils.auth_utils import requires_role
import hashlib

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Simple check for now (In prod use proper hashing e.g. bcrypt)
    if not username or not password:
        return jsonify({'error': 'Missing credentials'}), 400
        
    user = User.query.filter_by(username=username).first()
    
    if user:
        # Check password (assuming plain text or simple hash for dev)
        # In real scenario: check_password_hash(user.password_hash, password)
        if user.password_hash == password: # Simplified
            return jsonify({
                'token': f"mock-token-{user.id}", # Use JWT in real app
                'user': user.to_dict()
            })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'worker')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'User already exists'}), 400
        
    new_user = User(username=username, password_hash=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created', 'user': new_user.to_dict()}), 201
@bp.route('/users', methods=['GET'])
@requires_role('admin')
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@bp.route('/users/<int:user_id>/role', methods=['PUT'])
@requires_role('admin')
def update_user_role(user_id):
    data = request.get_json()
    new_role = data.get('role')
    if new_role not in ['worker', 'maintainer', 'admin']:
        return jsonify({'error': 'Invalid role'}), 400
        
    user = User.query.get_or_404(user_id)
    user.role = new_role
    db.session.commit()
    return jsonify(user.to_dict())
