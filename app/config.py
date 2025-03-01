import os

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///edutech.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")