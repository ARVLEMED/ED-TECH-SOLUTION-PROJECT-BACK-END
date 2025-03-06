## ED-TECH-SOLUTION-PROJECT-BACK-END

This is the back-end for an educational technology solution, built with Flask and Python. It provides a RESTful API to manage users, students, teachers, classes, subjects, exams, results, welfare reports, and forms, with features like JWT authentication, soft deletes, and database migrations.
# Table of Contents

    Features
    Technologies
    Project Structure
    Setup Instructions
    Running Locally
    Database Migrations
    API Endpoints
    Deployment on Render
    Environment Variables
    Contributing
    License

# Features

    User authentication with JWT
    Role-based access control (admin, teacher, parent)
    CRUD operations for students, teachers, classes, subjects, exams, results, and welfare reports
    Soft delete functionality for data persistence
    Many-to-many relationships (e.g., teachers-subjects, students-subjects)
    Database migrations with Flask-Migrate
    CORS support for frontend integration
    Logging for debugging

# Technologies

    Python: 3.12
    Flask: Web framework
    Flask-SQLAlchemy: ORM for database management
    Flask-Migrate: Database migrations
    Flask-Bcrypt: Password hashing
    Flask-JWT-Extended: JWT authentication
    Flask-Marshmallow: Object serialization
    Flask-CORS: Cross-Origin Resource Sharing
    PyJWT: JWT token generation and validation
    PostgreSQL: Production database (SQLite for development)
    Gunicorn: WSGI server for production
    Pipenv: Dependency management

# Project Structure
text
ED-TECH-SOLUTION-PROJECT-BACK-END/
├── app/
│   ├── __init__.py       # Flask app initialization
│   ├── config.py         # Configuration settings
│   ├── models.py         # Database models
│   ├── routes.py         # API routes
│   ├── schemas.py        # Marshmallow schemas for serialization
│   ├── migrations/       # Flask-Migrate migration files
│   └── run.py            # Entry point for the app
├── seed_data.py          # Script to seed mock data
├── .env                  # Environment variables (not tracked)
├── .gitignore            # Git ignore file
├── Pipfile              # Dependency manifest
├── Pipfile.lock         # Locked dependencies
├── Procfile             # Render process file
├── requirements.txt      # Dependencies for Render
└── README.md             # This file
# Setup Instructions
Prerequisites

    Python 3.12
    Pipenv (pip install pipenv)
    PostgreSQL (optional for local development; SQLite is default)

Installation

    Clone the repository:
    bash

git clone https://github.com/username/ED-TECH-SOLUTION-PROJECT-BACK-END.git
cd ED-TECH-SOLUTION-PROJECT-BACK-END
Install dependencies:
bash
pipenv install
Create a .env file: In the root directory, create a .env file with the following:
plaintext
DATABASE_URL=sqlite:///edutech.db  # or postgresql://user:password@localhost:5432/edutech
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
Replace values with your own secure keys and database URL.
Activate the virtual environment:
bash

    pipenv shell

Running Locally

    Seed the database (optional):
    bash

python app/run.py
This runs the app and seeds mock data. Comment out the seed_data() call in run.py after initial setup.
Start the Flask development server:
bash

    flask run
    The API will be available at http://localhost:5000/api.

Database Migrations

    Initialize migrations (first time only):
    bash

flask db init
Generate a migration:
bash
flask db migrate -m "your migration message"
Apply migrations:
bash
flask db upgrade
Revert migrations (if needed):
bash

    flask db downgrade

# API Endpoints

Below is a summary of key endpoints. All routes are prefixed with /api.
Method	Endpoint	Description	Roles
POST	/login	User login with JWT token	All
POST	/users	Create a new user	Public
GET	/users	List all users	Admin
GET	/students	List students	Teacher/Admin
POST	/students	Create a student	Admin
GET	/students/<id>	Get student details	Parent/Teacher/Admin
GET	/results	List results	Teacher/Admin
POST	/results	Create a result	Teacher
GET	/welfare_reports	List welfare reports	Teacher/Admin
POST	/welfare_reports	Create a welfare report	Teacher

    Authentication: Most endpoints require a JWT token in the Authorization header (e.g., Bearer <token>).
    Soft Deletes: Deleted records are marked with deleted_at and excluded from responses.

# Deployment on Render

    Push to GitHub:
    bash

git add .
git commit -m "Prepare for Render deployment"
git push origin main
Create a Web Service on Render:

    Go to Render, click "New" > "Web Service".
    Connect your GitHub repository.

# Configure Settings:

    Runtime: Python
    Build Command: pip install -r requirements.txt && flask db upgrade
    Start Command: gunicorn --chdir app run:app
    Add environment variables in the dashboard:
    plaintext

        DATABASE_URL=<render-postgres-url>
        SECRET_KEY=<random-string>
        JWT_SECRET_KEY=<random-string>
    Set Up PostgreSQL:
        Create a PostgreSQL database on Render.
        Use the internal connection string as DATABASE_URL.
    Deploy:
        Trigger a deployment. The API will be live at https://your-service.onrender.com/api.

# Environment Variables
Variable	Description	Default Value
DATABASE_URL	Database connection string	sqlite:///edutech.db
SECRET_KEY	Flask secret key	supersecretkey
JWT_SECRET_KEY	JWT secret key	jwtsecret

Store these in a .env file locally and in Render’s environment variables for production. Do not commit .env to Git.
Contributing

    Fork the repository.
    Create a feature branch (git checkout -b feature/your-feature).
    Commit changes (git commit -m "Add your feature").
    Push to the branch (git push origin feature/your-feature).
    Open a pull request.

## License

This project is licensed under the MIT License. See LICENSE for details (create this file if needed).