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
import os

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
    
    # Enhanced CORS configuration
    cors_options = {
        "origins": [
            "https://byte-force-ed-tech-app.netlify.app",  # No trailing slash
            "http://localhost:5173",  # For local development (adjust port if needed)
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly allow methods
        "allow_headers": ["Content-Type", "Authorization"],  # Allow JWT and content type headers
        "supports_credentials": True  # If you need cookies or auth credentials
    }
    CORS(app, resources={r"/api/*": cors_options})

    # Enable foreign keys for SQLite (optional, not needed for PostgreSQL on Render)
    @app.before_request
    def enable_foreign_keys():
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            db.session.execute(text('PRAGMA foreign_keys = ON'))

    # Error handler for debugging
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {str(e)}")
        return {"error": "Internal server error"}, 500

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

    # Log startup
    logger.info(f"Flask app started with environment: {os.getenv('FLASK_ENV', 'production')}")

    return app

# Optional: Add a simple health check route outside the blueprint
app = create_app()

@app.route('/health')
def health_check():
    return {"status": "healthy"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))