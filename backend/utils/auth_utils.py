from functools import wraps
from flask import request, jsonify
from models import User

def requires_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 在實際應用中，應驗證 JWT Token 並獲取使用者角色
            # 本 MVP 中，從 X-User-ID 或 Authorization 標頭獲取使用者資訊
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                # 處理前端發送的 'Bearer mock-token-ID' 格式
                token = request.headers.get('Authorization')
                if token:
                    if token.startswith('Bearer '):
                        token = token.replace('Bearer ', '')
                    if token.startswith('mock-token-'):
                        user_id = token.replace('mock-token-', '')
            
            if not user_id:
                return jsonify({'error': 'Unauthorized'}), 401
                
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 401
            
            # 角色權限階級檢查 (Role hierarchy check)
            # worker (0) < maintainer (1) < admin (2)
            role_hierarchy = {'worker': 0, 'maintainer': 1, 'admin': 2}
            user_level = role_hierarchy.get(user.role, 0)
            required_level = role_hierarchy.get(role, 0)
            
            if user_level < required_level:
                return jsonify({'error': 'Forbidden: Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
