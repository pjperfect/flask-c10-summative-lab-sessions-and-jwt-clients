"""
Application configuration settings.
"""

import os


class Config:
    """Base configuration shared across environments."""

    # Database — defaults to a local SQLite file; override via environment variable.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///productivity.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key used to sign the session cookie.
    # IMPORTANT: set a strong random value in production via the SECRET_KEY env var.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # Store sessions server-side in a signed cookie (Flask default).
    SESSION_TYPE = "filesystem"


class TestingConfig(Config):
    """Configuration used during automated tests."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False