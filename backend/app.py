import os
import uuid
import json
import random
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)

# ==========================================
# Mock Database (In-Memory)
# ==========================================

MOCK_DB = {
    "users": [
        {"id": 1, "username": "admin", "password_hash": "admin", "role": "admin"},
        {"id": 2, "username": "user", "password_hash": "user", "role": "worker"},
        {"id": 3, "username": "main", "password_hash": "main", "role": "maintainer"},
    ],
    "layouts": [
        {
            "id": "floor6-test",
            "name": "6F Test Area",
            "width": 1200,
            "height": 800,
            "floor": "6F",
            "area": "Test",
        }
    ],
    "components": [] # Populated in initialization below
}

# Add some initial components to the mock layout
MOCK_DB["components"] = [
    {
        "id": "comp-1",
        "layout_id": "floor6-test",
        "type": "bin",
        "x": 100, "y": 100, "width": 80, "height": 80, "rotation": 0,
        "code": "A-01",
        "shape_points": None,
        "props": json.dumps({"color": "#4dabf7"})
    },
    {
        "id": "comp-2",
        "layout_id": "floor6-test",
        "type": "bin",
        "x": 200, "y": 100, "width": 80, "height": 80, "rotation": 0,
        "code": "A-02",
        "shape_points": None,
        "props": json.dumps({"color": "#4dabf7"})
    }
]

# ==========================================
# Mock pyodbc Implementation
# ==========================================

class MockCursor:
    def __init__(self):
        self._data = []
        self._index = 0
        self.description = []

    def execute(self, sql, params=None):
        sql = sql.lower()
        # Simplified parser for mock data
        if "select" in sql and "users" in sql:
            if "where username =" in sql:
                uname = params[0]
                self._data = [u for u in MOCK_DB["users"] if u["username"] == uname]
            else:
                self._data = MOCK_DB["users"]
        
        elif "select" in sql and "layouts" in sql:
            if "where id =" in sql:
                lid = params[0]
                self._data = [l for l in MOCK_DB["layouts"] if l["id"] == lid]
            else:
                self._data = MOCK_DB["layouts"]
                
        elif "select" in sql and "components" in sql:
            if "where layout_id =" in sql:
                lid = params[0]
                self._data = [c for c in MOCK_DB["components"] if c["layout_id"] == lid]
            elif "where id =" in sql:
                cid = params[0]
                self._data = [c for c in MOCK_DB["components"] if c["id"] == cid]
            else:
                self._data = MOCK_DB["components"]
        
        elif "insert into components" in sql:
            # params order: id, layout_id, type, x, y, width, height, rotation, code, shape_points, props
            new_comp = {
                "id": params[0],
                "layout_id": params[1],
                "type": params[2],
                "x": params[3],
                "y": params[4],
                "width": params[5],
                "height": params[6],
                "rotation": params[7],
                "code": params[8],
                "shape_points": params[9],
                "props": params[10]
            }
            MOCK_DB["components"].append(new_comp)
            self._data = []
            
        elif "update components" in sql:
            # Simplified update
            cid = params[-1]
            for c in MOCK_DB["components"]:
                if c["id"] == cid:
                    # In a real pyodbc, we'd map params to columns. Here we just assume it's updating everything.
                    # This mock is very simplified.
                    pass
            self._data = []

        elif "delete from components" in sql:
            cid = params[0]
            MOCK_DB["components"] = [c for c in MOCK_DB["components"] if c["id"] != cid]
            self._data = []

        self._index = 0
        return self

    def fetchall(self):
        return self._data

    def fetchone(self):
        if self._index < len(self._data):
            res = self._data[self._index]
            self._index += 1
            return res
        return None

    def commit(self):
        pass

class MockConnection:
    def cursor(self):
        return MockCursor()
    def commit(self):
        pass
    def close(self):
        pass

# Mock the pyodbc.connect function
def pyodbc_connect(connection_string):
    return MockConnection()

# ==========================================
# Auth Utils
# ==========================================

def get_current_user_role():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer mock-token-'):
        user_id = int(token.replace('Bearer mock-token-', ''))
        user = next((u for u in MOCK_DB["users"] if u["id"] == user_id), None)
        if user:
            return user["role"]
    return None

def requires_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = get_current_user_role()
            if not user_role:
                return jsonify({'error': 'Unauthorized'}), 401
            
            role_hierarchy = {'worker': 0, 'maintainer': 1, 'admin': 2}
            user_level = role_hierarchy.get(user_role, 0)
            required_level = role_hierarchy.get(role, 0)
            
            if user_level < required_level:
                return jsonify({'error': 'Forbidden: Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==========================================
# Routes
# ==========================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = pyodbc_connect("") # Mock
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user and user["password_hash"] == password:
        return jsonify({
            'token': f"mock-token-{user['id']}",
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        })
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/layouts', methods=['GET'])
def get_layouts():
    conn = pyodbc_connect("")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM layouts")
    layouts = cursor.fetchall()
    return jsonify(layouts)

@app.route('/api/layouts/<layout_id>', methods=['GET'])
def get_layout(layout_id):
    conn = pyodbc_connect("")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM layouts WHERE id = ?", (layout_id,))
    layout = cursor.fetchone()
    
    if not layout:
        return jsonify({"error": "Layout not found"}), 404
        
    cursor.execute("SELECT * FROM components WHERE layout_id = ?", (layout_id,))
    components = cursor.fetchall()
    
    result = layout.copy()
    # Format components for frontend
    result['components'] = []
    for c in components:
        comp_dict = c.copy()
        if 'shape_points' in comp_dict and comp_dict['shape_points']:
            comp_dict['shapePoints'] = json.loads(comp_dict['shape_points'])
        if 'props' in comp_dict and comp_dict['props']:
            comp_dict['props'] = json.loads(comp_dict['props'])
        result['components'].append(comp_dict)
        
    return jsonify(result)

@app.route('/api/layouts/<layout_id>/components', methods=['POST'])
@requires_role('maintainer')
def add_component(layout_id):
    data = request.get_json()
    comp_id = str(uuid.uuid4())
    
    # SQL query simulation
    sql = "INSERT INTO components (id, layout_id, type, x, y, width, height, rotation, code, shape_points, props) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    params = (
        comp_id, layout_id, data.get('type'), 
        data.get('x', 0), data.get('y', 0), 
        data.get('width', 100), data.get('height', 100), 
        data.get('rotation', 0), data.get('code'),
        json.dumps(data.get('shapePoints')) if data.get('shapePoints') else None,
        json.dumps(data.get('props')) if data.get('props') else '{}'
    )
    
    conn = pyodbc_connect("")
    cursor = conn.cursor()
    cursor.execute(sql, params)
    
    return jsonify({"id": comp_id, "layoutId": layout_id, **data}), 201

@app.route('/api/data/wip', methods=['POST'])
def get_wip_data():
    data = request.get_json()
    bin_codes = data.get('binCodes', [])
    
    results = {}
    for code in bin_codes:
        if random.random() > 0.9:
            results[code] = []
            continue
            
        cassettes = []
        for i in range(random.randint(1, 4)):
            cst_id = f"CST-{random.randint(1000, 9999)}"
            wips = []
            for j in range(random.randint(5, 15)):
                wips.append({
                    'sheet_id_chip_id': f"S{random.randint(10,99)}-CH{random.randint(100,999)}",
                    'grade': random.choice(['A', 'B', 'P']),
                    'model_no': random.choice(['TX-2024', 'RX-9900', 'AI-CHIP']),
                    'stage_id': random.choice(['LITH', 'ETCH', 'DEP']),
                    'op_id': f"OP-{random.randint(200, 500)}"
                })
            cassettes.append({
                'cassette_id': cst_id,
                'position': i + 1,
                'wips': wips
            })
        results[code] = cassettes
    
    return jsonify(results)

@app.route('/api/data/counts', methods=['POST'])
def get_bin_counts():
    data = request.get_json()
    bin_codes = data.get('binCodes', [])
    results = {code: random.randint(1, 5) for code in bin_codes}
    return jsonify(results)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "mode": "DEV-MOCK-SQL"})

if __name__ == '__main__':
    print("Backend running on http://localhost:5000 (Mock SQL Mode)")
    app.run(debug=True, port=5000)
