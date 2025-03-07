# app/config.py
import os
from dotenv import load_dotenv

# Load .env file for local development (optional on Render)
load_dotenv()

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Use DATABASE_URL from environment, with fallback to SQLite for local dev
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///edutech.db").replace("postgres://", "postgresql://")
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt_secret_key")