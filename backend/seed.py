from app import create_app
from models import db, Layout, Component, User
import uuid

def seed_data():
    app = create_app('development')
    with app.app_context():
        # Clear existing
        db.drop_all()
        db.create_all()
        
        # Create Users
        admin = User(username='admin', password_hash='admin', role='admin')
        worker = User(username='worker', password_hash='worker', role='worker')
        maintainer = User(username='maintainer', password_hash='maintainer', role='maintainer')
        db.session.add_all([admin, worker, maintainer])
        
        # Create Layouts
        layouts_info = [
            {'name': '大R區 (Big R)', 'floor': '1F', 'area': 'Big R'},
            {'name': '5F測試區 (5F Test Area)', 'floor': '5F', 'area': 'Test'},
            {'name': '6F測試區 (6F Test Area)', 'floor': '6F', 'area': 'Test'},
            {'name': '6F雷射維修區 (6F Laser Repair)', 'floor': '6F', 'area': 'Laser'},
            {'name': '7F雷射維修區 (7F Laser Repair)', 'floor': '7F', 'area': 'Laser'},
            {'name': '7F非測試區 (7F Non-Test)', 'floor': '7F', 'area': 'Production'}
        ]
        
        for info in layouts_info:
            layout_id = str(uuid.uuid4())
            layout = Layout(
                id=layout_id,
                name=info['name'],
                width=1200,
                height=800,
                floor=info['floor'],
                area=info['area']
            )
            db.session.add(layout)
            
            # Add diverse components
            # 1. Standard Rect Bins
            for i in range(1, 11):
                db.session.add(Component(
                    id=str(uuid.uuid4()),
                    layout_id=layout_id,
                    type='bin',
                    x=50 + (i-1)*110, y=100, width=80, height=80,
                    code=f"{info['floor']}-B-{i:02d}",
                    props='{"color": "#334155"}'
                ))

            # 2. Pillars (Non-interactive structural elements)
            for i in range(1, 4):
                db.session.add(Component(
                    id=str(uuid.uuid4()),
                    layout_id=layout_id,
                    type='pillar',
                    x=200 + i*300, y=400, width=40, height=40,
                    code=f"P-{i}",
                    props='{"color": "#94a3b8"}'
                ))

            # 3. Polygon Bins (Hexagons or custom shapes) for variety
            if '測試區' in info['name'] or '大R區' in info['name']:
                points = [{"x":40,"y":0},{"x":80,"y":20},{"x":80,"y":60},{"x":40,"y":80},{"x":0,"y":60},{"x":0,"y":20}]
                import json
                db.session.add(Component(
                    id=str(uuid.uuid4()),
                    layout_id=layout_id,
                    type='bin',
                    x=100, y=600,
                    code=f"{info['floor']}-HEX-01",
                    shape_points=json.dumps(points),
                    props='{"color": "#1e293b"}'
                ))

        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_data()
