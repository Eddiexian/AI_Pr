from flask import Blueprint, request, jsonify
from models import db, Layout, Component
from utils.auth_utils import requires_role
import uuid
import json

bp = Blueprint('layout', __name__, url_prefix='/api/layouts')

@bp.route('/', methods=['GET'])
def get_layouts():
    layouts = Layout.query.all()
    return jsonify([l.to_dict() for l in layouts])

@bp.route('/', methods=['POST'])
@requires_role('maintainer')
def create_layout():
    data = request.get_json()
    layout = Layout(
        id=str(uuid.uuid4()),
        name=data.get('name'),
        width=data.get('width', 800),
        height=data.get('height', 600),
        floor=data.get('floor'),
        area=data.get('area')
    )
    db.session.add(layout)
    db.session.commit()
    return jsonify(layout.to_dict()), 201

@bp.route('/<layout_id>', methods=['GET'])
def get_layout(layout_id):
    layout = Layout.query.get_or_404(layout_id)
    components = Component.query.filter_by(layout_id=layout_id).all()
    result = layout.to_dict()
    result['components'] = [c.to_dict() for c in components]
    return jsonify(result)

@bp.route('/<layout_id>', methods=['PUT'])
@requires_role('maintainer')
def update_layout(layout_id):
    layout = Layout.query.get_or_404(layout_id)
    data = request.get_json()
    
    if 'name' in data: layout.name = data['name']
    if 'width' in data: layout.width = data['width']
    if 'height' in data: layout.height = data['height']
    
    db.session.commit()
    return jsonify(layout.to_dict())

@bp.route('/<layout_id>', methods=['DELETE'])
@requires_role('maintainer')
def delete_layout(layout_id):
    layout = Layout.query.get_or_404(layout_id)
    db.session.delete(layout)
    db.session.commit()
    return jsonify({'message': 'Layout deleted'})

# Component Routes
@bp.route('/<layout_id>/components', methods=['POST'])
@requires_role('maintainer')
def add_component(layout_id):
    data = request.get_json()
    comp = Component(
        id=str(uuid.uuid4()),
        layout_id=layout_id,
        type=data.get('type'),
        x=data.get('x', 0),
        y=data.get('y', 0),
        width=data.get('width', 100),
        height=data.get('height', 100),
        rotation=data.get('rotation', 0),
        code=data.get('code'),
        # Handle complex shape points
        shape_points=json.dumps(data.get('shapePoints')) if data.get('shapePoints') else None,
        props=json.dumps(data.get('props')) if data.get('props') else '{}'
    )
    db.session.add(comp)
    db.session.commit()
    return jsonify(comp.to_dict()), 201

@bp.route('/components/<component_id>', methods=['PUT'])
@requires_role('maintainer')
def update_component(component_id):
    comp = Component.query.get_or_404(component_id)
    data = request.get_json()
    
    if 'x' in data: comp.x = data['x']
    if 'y' in data: comp.y = data['y']
    if 'width' in data: comp.width = data['width']
    if 'height' in data: comp.height = data['height']
    if 'rotation' in data: comp.rotation = data['rotation']
    if 'shapePoints' in data: comp.shape_points = json.dumps(data['shapePoints'])
    if 'props' in data: comp.props = json.dumps(data['props'])
    
    db.session.commit()
    return jsonify(comp.to_dict())

@bp.route('/components/<component_id>', methods=['DELETE'])
@requires_role('maintainer')
def delete_component(component_id):
    comp = Component.query.get_or_404(component_id)
    db.session.delete(comp)
    db.session.commit()
    return jsonify({'message': 'Component deleted'})
