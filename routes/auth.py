"""
Authentication routes.

Endpoints
---------
POST   /signup          — register a new user
POST   /login           — authenticate and start a session
DELETE /logout          — end the current session
GET    /check_session   — return the logged-in user (or 401)
"""

from flask import Blueprint, request, session, jsonify
from models import db, User

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def current_user():
    """Return the User for the active session, or None."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db.session.get(User, user_id)


# ---------------------------------------------------------------------------
# POST /signup
# ---------------------------------------------------------------------------

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    Create a new account.

    Expects JSON: { "username": "...", "password": "..." }
    Returns 201 with user data on success, 422 on validation errors.
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username:
        return jsonify({"error": "username is required"}), 422
    if not password:
        return jsonify({"error": "password is required"}), 422

    # Enforce uniqueness at the application layer for a clear error message.
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username already taken"}), 422

    user = User(username=username)
    user.password = password  # triggers bcrypt hashing via the setter
    db.session.add(user)
    db.session.commit()

    # Log the new user in immediately.
    session["user_id"] = user.id

    return jsonify(user.to_dict()), 201


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user and start a session.

    Expects JSON: { "username": "...", "password": "..." }
    Returns 200 with user data, or 401 on bad credentials.
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "invalid username or password"}), 401

    session["user_id"] = user.id
    return jsonify(user.to_dict()), 200


# ---------------------------------------------------------------------------
# DELETE /logout
# ---------------------------------------------------------------------------

@auth_bp.route("/logout", methods=["DELETE"])
def logout():
    """
    End the current session.

    Returns 204 No Content regardless of whether a session was active.
    """
    session.pop("user_id", None)
    return "", 204


# ---------------------------------------------------------------------------
# GET /check_session
# ---------------------------------------------------------------------------

@auth_bp.route("/check_session", methods=["GET"])
def check_session():
    """
    Return the currently authenticated user.

    Returns 200 with user data if logged in, 401 otherwise.
    This endpoint is used by the frontend on page refresh to restore auth state.
    """
    user = current_user()
    if user is None:
        return jsonify({"error": "not authenticated"}), 401
    return jsonify(user.to_dict()), 200