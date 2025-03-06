from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_jwt_extended import JWTManager  # Add JWTManager
from sqlalchemy.sql import text  # Import text for SQL expressions
import logging  # Add logging for debugging

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
ma = Marshmallow()
jwt = JWTManager()  # Initialize JWTManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Enable debug logging
logger = logging.getLogger(__name__)

def create_app(config_class="app.config.Config"):
    # Create and configure the Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = 'jwtsecret'  # Replace with a secure key
    app.config['DEBUG'] = True  # Enable debug mode for detailed errors

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)  # Initialize JWTManager with the app
    CORS(app, resources={r"/api/*": {"origins": "https://byte-force-ed-tech.netlify.app/"}})

    # Enable foreign keys for SQLite using text()
    @app.before_request
    def enable_foreign_keys():
        db.session.execute(text('PRAGMA foreign_keys = ON'))
        

    # Import models and routes within the app context
    with app.app_context():
        from app.models import User, Teacher, Student, SchoolClass, Subject, Exam, Result, WelfareReport, Form, TeacherSubject
        from app.routes import api_bp  # Import routes

        # Register the blueprint with the API prefix
        app.register_blueprint(api_bp, url_prefix='/api')

        # Create database tables if they don't exist
        try:
            db.create_all()
            logger.debug("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")

    return app