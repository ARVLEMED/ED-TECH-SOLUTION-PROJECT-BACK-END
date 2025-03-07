# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.sql import text
import logging

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
ma = Marshmallow()
jwt_manager = JWTManager()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    # Create and configure the Flask app
    app = Flask(__name__)
    # Import Config directly instead of using a string
    from .config import Config
    app.config.from_object(Config)

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    ma.init_app(app)
    jwt_manager.init_app(app)
    
    # CORS: Allow Render frontend (adjust as needed)
    CORS(app, resources={r"/api/*": {"origins": ["https://byte-force-ed-tech.netlify.app", "http://localhost:3000"]}})

    # Enable foreign keys for SQLite (optional, not needed for PostgreSQL on Render)
    @app.before_request
    def enable_foreign_keys():
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            db.session.execute(text('PRAGMA foreign_keys = ON'))

    # Import models and routes within the app context
    with app.app_context():
        from .models import User, Teacher, Student, SchoolClass, Subject, Exam, Result, WelfareReport, Form, TeacherSubject
        from .routes import api_bp

        # Register the blueprint
        app.register_blueprint(api_bp, url_prefix='/api')

        # Create database tables
        try:
            db.create_all()
            logger.debug("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")

    return app