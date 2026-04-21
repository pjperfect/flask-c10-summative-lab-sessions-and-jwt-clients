"""
Application entry-point.

Creates and configures the Flask app, registers extensions and blueprints,
and exposes the `app` object used by Flask's CLI (flask run) and the
migration commands (flask db ...).
"""

from flask import Flask
from flask_migrate import Migrate
from config import Config
from models import db, bcrypt
from routes.auth import auth_bp

migrate = Migrate()


def create_app(config_class=Config):
    """Application factory. Pass a different config class for testing."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ----- Extensions -----
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # ----- Blueprints -----
    app.register_blueprint(auth_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)