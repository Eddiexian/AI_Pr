from models import User, db

def test_login_success(client, app):
    # Create a user first
    with app.app_context():
        user = User(username='testuser')
        user.password_hash = 'password123'
        db.session.add(user)
        db.session.commit()

    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    assert 'token' in response.json
    assert response.json['user']['username'] == 'testuser'

def test_login_failure(client):
    response = client.post('/api/auth/login', json={
        'username': 'wronguser',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401
