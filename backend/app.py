from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from models import db, User, Layout, Component

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    CORS(app)
    db.init_app(app)
    
    from routes import auth, layout, data
    app.register_blueprint(auth.bp)
    app.register_blueprint(layout.bp)
    app.register_blueprint(data.bp)
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy", "mode": app.config['MODE']})
        
    with app.app_context():
        # Create Tables if they don't exist (Useful for Dev/SQLite)
        if app.config.get('MODE') == 'DEV':
            db.create_all()
            
    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, port=5000)
