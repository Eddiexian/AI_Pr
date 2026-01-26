import uuid
import json
import random
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)

# ==========================================
# DB Connection Config (你的設定)
# ==========================================

DB_CONFIG = {
    "server": r"TW100039277\PC05SQLSERVER",
    "database": "BoxPositionSys",
    "username": "sa",
    "password": "9ol.)P:?"
}

def get_connection():
    return pyodbc.connect(
        f"DRIVER={{SQL Server}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']}"
        # 如果需要可加上 ;TrustServerCertificate=yes
    )

# ==========================================
# Helper: row 轉 dict
# ==========================================

def rows_to_dicts(cursor, rows):
    if not rows:
        return []
    columns = [col[0] for col in cursor.description]
    result = []
    for row in rows:
        d = {}
        for col, val in zip(columns, row):
            d[col] = val
        result.append(d)
    return result

def row_to_dict(cursor, row):
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return {col: val for col, val in zip(columns, row)}

# ==========================================
# Auth Utils
# ==========================================

def get_current_user_role():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer mock-token-'):
        try:
            user_id = int(token.replace('Bearer mock-token-', ''))
        except ValueError:
            return None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
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
# Auth Routes
# ==========================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    username = data.get('username')
    password = data.get('password')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username = ?",
        (username,)
    )
    row = cursor.fetchone()
    conn.close()

    user = row_to_dict(cursor, row) if row else None

    # 目前仍以明碼比對，實務建議改用雜湊
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

@app.route('/api/auth/verify', methods=['GET'])
def verify_token():
    token = request.headers.get('Authorization')

    if not token or not token.startswith('Bearer mock-token-'):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user_id = int(token.replace('Bearer mock-token-', ''))
    except ValueError:
        return jsonify({'error': 'Invalid token format'}), 401

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'User not found'}), 404

    user = row_to_dict(cursor, row)

    return jsonify({
        'user': {
            'id': user['id'],
            'username': user['username'],
            'role': user['role']
        }
    })

# ==========================================
# Layout Routes
# ==========================================

from datetime import datetime  # 如果之後要加時間欄位可用，現在先保留可不加

@app.route('/api/layouts', methods=['POST'])
@requires_role('maintainer')  # 或 'admin'，視你權限需求
def create_layout():
    data = request.get_json(force=True)
    name = data.get('name')
    if not name:
        return jsonify({"error": "name is required"}), 400

    # 給 layout 一個 id，如果你希望自訂格式可以調整這裡
    layout_id = data.get('id') or f"layout-{uuid.uuid4().hex[:8]}"

    width = data.get('width', 1200)
    height = data.get('height', 800)
    floor = data.get('floor', '')
    area = data.get('area', '')

    conn = get_connection()
    cursor = conn.cursor()

    # 檢查是否重複 id
    cursor.execute("SELECT 1 FROM layouts WHERE id = ?", (layout_id,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "layout id already exists"}), 400

    cursor.execute(
        """
        INSERT INTO layouts (id, name, width, height, floor, area)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (layout_id, name, width, height, floor, area)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "id": layout_id,
        "name": name,
        "width": width,
        "height": height,
        "floor": floor,
        "area": area
    }), 201


@app.route('/api/layouts/<layout_id>', methods=['DELETE'])
@requires_role('admin')
def delete_layout(layout_id):
    conn = get_connection()
    cursor = conn.cursor()

    # 先刪 components（外鍵關係）
    cursor.execute("DELETE FROM components WHERE layout_id = ?", (layout_id,))

    # 再刪 layout
    cursor.execute("DELETE FROM layouts WHERE id = ?", (layout_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    if affected == 0:
        return jsonify({"error": "Layout not found"}), 404

    return jsonify({"status": "deleted", "id": layout_id})


@app.route('/api/layouts', methods=['GET'])
def get_layouts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, width, height, floor, area FROM layouts")
    rows = cursor.fetchall()
    conn.close()

    layouts = rows_to_dicts(cursor, rows)
    return jsonify(layouts)

@app.route('/api/layouts/<layout_id>', methods=['GET'])
def get_layout(layout_id):
    conn = get_connection()
    cursor = conn.cursor()

    # 讀 layout
    cursor.execute(
        "SELECT id, name, width, height, floor, area FROM layouts WHERE id = ?",
        (layout_id,)
    )
    row = cursor.fetchone()
    layout = row_to_dict(cursor, row) if row else None

    if not layout:
        conn.close()
        return jsonify({"error": "Layout not found"}), 404

    # 讀 components
    cursor.execute("""
        SELECT id, layout_id, type, x, y, width, height, rotation, code, shape_points, props
        FROM components WHERE layout_id = ?
    """, (layout_id,))
    comp_rows = cursor.fetchall()
    components = rows_to_dicts(cursor, comp_rows)
    conn.close()

    # 格式化給前端
    formatted_components = []
    for c in components:
        comp_dict = dict(c)

        # DB 欄位為 shape_points，前端用 shapePoints
        if comp_dict.get('shape_points'):
            try:
                comp_dict['shapePoints'] = json.loads(comp_dict['shape_points'])
            except Exception:
                comp_dict['shapePoints'] = None
        else:
            comp_dict['shapePoints'] = None

        # props JSON
        if comp_dict.get('props'):
            try:
                comp_dict['props'] = json.loads(comp_dict['props'])
            except Exception:
                comp_dict['props'] = {}
        else:
            comp_dict['props'] = {}

        formatted_components.append(comp_dict)

    layout['components'] = formatted_components
    return jsonify(layout)

@app.route('/api/layouts/<layout_id>', methods=['PUT'])
@requires_role('maintainer')
def update_layout(layout_id):
    data = request.get_json(force=True)
    width = data.get('width')
    height = data.get('height')

    if width is None or height is None:
        return jsonify({"error": "Width and height are required"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE layouts SET width = ?, height = ? WHERE id = ?",
        (width, height, layout_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Layout not found"}), 404

    conn.commit()
    conn.close()
    return jsonify({"id": layout_id, "width": width, "height": height})

# ==========================================
# Component Routes (Create / Update / Delete)
# ==========================================

@app.route('/api/layouts/<layout_id>/components', methods=['POST'])
@requires_role('maintainer')
def add_component(layout_id):
    data = request.get_json(force=True)
    comp_id = str(uuid.uuid4())

    shape_points_json = json.dumps(data.get('shapePoints')) if data.get('shapePoints') else None
    props_json = json.dumps(data.get('props')) if data.get('props') else '{}'

    sql = """
        INSERT INTO components
        (id, layout_id, type, x, y, width, height, rotation, code, shape_points, props)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        comp_id,
        layout_id,
        data.get('type'),
        data.get('x', 0),
        data.get('y', 0),
        data.get('width', 100),
        data.get('height', 100),
        data.get('rotation', 0),
        data.get('code'),
        shape_points_json,
        props_json
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    conn.close()

    return jsonify({"id": comp_id, "layoutId": layout_id, **data}), 201

@app.route('/api/components/<component_id>', methods=['PUT', 'PATCH'])
@requires_role('maintainer')
def update_component(component_id):
    data = request.get_json(force=True)

    fields = []
    params = []

    # 允許更新的欄位
    updatable_fields = ['type', 'x', 'y', 'width', 'height', 'rotation', 'code', 'shapePoints', 'props']

    for key in updatable_fields:
        if key in data:
            if key == 'shapePoints':
                fields.append("shape_points = ?")
                params.append(json.dumps(data['shapePoints']) if data['shapePoints'] is not None else None)
            elif key == 'props':
                fields.append("props = ?")
                params.append(json.dumps(data['props']) if data['props'] is not None else '{}')
            else:
                fields.append(f"{key} = ?")
                params.append(data[key])

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    sql = f"UPDATE components SET {', '.join(fields)} WHERE id = ?"
    params.append(component_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    conn.close()

    return jsonify({"id": component_id, **data})

@app.route('/api/components/<component_id>', methods=['DELETE'])
@requires_role('maintainer')
def delete_component(component_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM components WHERE id = ?", (component_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted", "id": component_id})

# ==========================================
# Mock Data Routes (仍使用隨機資料)
# ==========================================
@app.route('/api/data/wip', methods=['POST'])
def get_wip_data():
    data = request.get_json(force=True)
    bin_codes = data.get('binCodes', [])

    if not bin_codes:
        return jsonify({})

    conn = get_connection()
    cursor = conn.cursor()

    # 這裡的 position 對應的是 bin_code（前端的儲位代碼）
    # 你要產生 position in ('BIN1','BIN2',...) 放到 Oracle 那段 SQL 裡
    bin_list_str = ",".join(f"''{code}''" for code in bin_codes)

    # 注意：openquery 內部是 Oracle 的 SQL，字串要在 Python 這層組好
    sql = f"""
        SELECT *
        FROM OPENQUERY(ORACLELINK, '
            SELECT 
                a.position AS bin_code,
                a.cassette_id,
                1 AS cassette_position,
                b.sheet_id_chip_id,
                b.grade,
                b.model_no,
                b.stage_id,
                b.op_id
            FROM beolpptsn.r_cst_cst a
            LEFT JOIN celods.r_chip_wip_ods b
                ON a.cassette_id = b.cassette_id
            WHERE a.position IN ({bin_list_str})
            ORDER BY a.position, a.cassette_id, sheet_id_chip_id
        ');
    """

    # 注意：這裡已經沒有 ? 參數了，所以 execute 不需要 bin_codes
    cursor.execute(sql)
    rows = cursor.fetchall()

    # 將結果整理成前端要的結構
    results = {code: [] for code in bin_codes}

    # 結構: { bin_code: { cassette_id: { cassette_id, position, wips: [] } } }
    temp = {}

    for row in rows:
        # 這裡的屬性名稱要跟 SELECT 出來的欄位名一致
        # pyodbc 對大小寫不敏感，但你要確認實際 columnName
        bin_code = row.BIN_CODE
        cassette_id = row.CASSETTE_ID
        position = row.CASSETTE_POSITION or 1

        if bin_code not in temp:
            temp[bin_code] = {}

        if cassette_id not in temp[bin_code]:
            temp[bin_code][cassette_id] = {
                'cassette_id': cassette_id,
                'position': position,
                'wips': []
            }

        # 有可能某些 cassette 沒對應到 b（左聯結），row.sheet_id_chip_id 會是 None
        # 這種情況 wips 可以是空陣列
        if row.SHEET_ID_CHIP_ID:
            wip = {
                'sheet_id_chip_id': row.SHEET_ID_CHIP_ID,
                'grade': row.GRADE,
                'model_no': row.MODEL_NO,
                'stage_id': row.STAGE_ID,
                'op_id': row.OP_ID
            }
            temp[bin_code][cassette_id]['wips'].append(wip)

    # 組回 { bin_code: [ cassette1, cassette2, ... ] } 給前端
    for bin_code, cst_map in temp.items():
        results[bin_code] = list(cst_map.values())

    conn.close()
    return jsonify(results)

@app.route('/api/data/cassette-counts', methods=['POST'])
def get_cassette_counts():
    data = request.get_json(force=True)
    bin_codes = data.get('binCodes', [])

    if not bin_codes:
        return jsonify({})

    conn = get_connection()
    cursor = conn.cursor()

    # "BIN1","BIN2",... → 內層 Oracle SQL 需要兩層單引號
    bin_list_str = ",".join(f"''{code}''" for code in bin_codes)

    sql = f"""
        SELECT *
        FROM OPENQUERY(ORACLELINK, '
            SELECT 
                a.position AS bin_code,
                COUNT(DISTINCT a.cassette_id) AS cassette_count
            FROM beolpptsn.r_cst_cst a
            WHERE a.position IN ({bin_list_str})
            GROUP BY a.position
        ');
    """

    cursor.execute(sql)
    rows = cursor.fetchall()

    # 預設先全部 0，避免有些 bin 沒資料時 key 不存在
    results = {code: 0 for code in bin_codes}

    for row in rows:
      # 注意大小寫：BIN_CODE / CASSETTE_COUNT 這兩個欄位名要跟上面 SELECT 的 alias 完全一致
        bin_code = row.BIN_CODE
        cassette_count = row.CASSETTE_COUNT
        results[bin_code] = int(cassette_count or 0)

    conn.close()
    return jsonify(results)


@app.route('/api/data/counts', methods=['POST'])
def get_bin_counts():
    data = request.get_json(force=True)
    bin_codes = data.get('binCodes', [])
    results = {code: random.randint(1, 5) for code in bin_codes}
    return jsonify(results)


@app.route('/api/data/locate', methods=['POST'])
def locate_wip():
    data = request.get_json(force=True)
    chip_id = (data.get('chipId') or '').strip()
    cassette_id = (data.get('cassetteId') or '').strip()

    if not chip_id and not cassette_id:
        return jsonify({})

    conn = get_connection()
    cursor = conn.cursor()

    # 兩種查詢條件：
    # 1) 只給 cassette_id
    # 2) 給 chip_id（必要時 join 到 cassette）
    where_clauses = []
    if cassette_id:
      # a.cassette_id 直接對 cassette
        where_clauses.append(f" a.cassette_id = ''{cassette_id}'' ")
    if chip_id:
      # 依照你 wip 表的實際欄位名調整，這裡用 sheet_id_chip_id 為例
        where_clauses.append(f" b.sheet_id_chip_id = ''{chip_id}'' ")

    where_str = " AND ".join(where_clauses)

    sql = f"""
        SELECT *
        FROM OPENQUERY(ORACLELINK, '
            SELECT 
                a.position AS bin_code,
                a.cassette_id,
                b.sheet_id_chip_id
            FROM beolpptsn.r_cst_cst a
            LEFT JOIN celods.r_chip_wip_ods b
                ON a.cassette_id = b.cassette_id
            WHERE {where_str}
        ');
    """

    cursor.execute(sql)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({})

    result = {
        "bin_code": row.BIN_CODE,
        "cassette_id": row.CASSETTE_ID,
        "chip_id": getattr(row, 'SHEET_ID_CHIP_ID', None)
    }
    return jsonify(result)

# ==========================================
# Health Check
# ==========================================

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "mode": "SQL-SERVER"})

if __name__ == '__main__':
    app.run(host='10.96.45.146', port=4077, debug=True)
