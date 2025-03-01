from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
ma = Marshmallow()

def create_app(config_class="app.config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    ma.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})


    with app.app_context():
        from app.routes import api_bp  # Import routes
        app.register_blueprint(api_bp, url_prefix='/api')  # ✅ Register blueprint with prefix
    
    return app
