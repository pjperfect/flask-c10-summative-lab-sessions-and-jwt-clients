"""
Notes resource routes (protected — requires an active session).

Endpoints
---------
GET    /notes           — paginated list of the current user's notes
POST   /notes           — create a new note
PATCH  /notes/<id>      — update an existing note (owner only)
DELETE /notes/<id>      — delete a note (owner only)
"""

from flask import Blueprint, request, session, jsonify
from models import db, Note, User

notes_bp = Blueprint("notes", __name__)

# Default and maximum page sizes for pagination.
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


# ---------------------------------------------------------------------------
# Helper — enforce authentication on every notes route
# ---------------------------------------------------------------------------

def get_authenticated_user():
    """
    Look up the user from the session.

    Returns a (user, None) tuple on success, or (None, error_response) when
    the request is unauthenticated.
    """
    user_id = session.get("user_id")
    if not user_id:
        return None, (jsonify({"error": "authentication required"}), 401)

    user = db.session.get(User, user_id)
    if not user:
        # Session references a deleted user — clear it.
        session.pop("user_id", None)
        return None, (jsonify({"error": "authentication required"}), 401)

    return user, None


# ---------------------------------------------------------------------------
# GET /notes   (paginated)
# ---------------------------------------------------------------------------

@notes_bp.route("/notes", methods=["GET"])
def get_notes():
    """
    Return a paginated list of the authenticated user's notes.

    Query parameters
    ----------------
    page  : int  — 1-based page number (default 1)
    per_page : int — results per page (default 10, max 50)

    Response
    --------
    {
        "notes": [...],
        "page": 1,
        "per_page": 10,
        "total": 42,
        "pages": 5
    }
    """
    user, err = get_authenticated_user()
    if err:
        return err

    # Parse and clamp pagination parameters.
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(MAX_PAGE_SIZE, max(1, int(request.args.get("per_page", DEFAULT_PAGE_SIZE))))
    except (TypeError, ValueError):
        return jsonify({"error": "page and per_page must be integers"}), 422

    pagination = (
        Note.query
        .filter_by(user_id=user.id)
        .order_by(Note.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        "notes": [n.to_dict() for n in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }), 200


# ---------------------------------------------------------------------------
# POST /notes
# ---------------------------------------------------------------------------

@notes_bp.route("/notes", methods=["POST"])
def create_note():
    """
    Create a new note for the authenticated user.

    Expects JSON: { "title": "...", "content": "..." }
    Returns 201 with the created note.
    """
    user, err = get_authenticated_user()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title:
        return jsonify({"error": "title is required"}), 422
    if not content:
        return jsonify({"error": "content is required"}), 422

    note = Note(title=title, content=content, user_id=user.id)
    db.session.add(note)
    db.session.commit()

    return jsonify(note.to_dict()), 201


# ---------------------------------------------------------------------------
# PATCH /notes/<id>
# ---------------------------------------------------------------------------

@notes_bp.route("/notes/<int:note_id>", methods=["PATCH"])
def update_note(note_id):
    """
    Update the title and/or content of a note.

    Only the owner of the note may update it.
    Expects JSON with at least one of: { "title": "...", "content": "..." }
    Returns 200 with the updated note.
    """
    user, err = get_authenticated_user()
    if err:
        return err

    note = db.session.get(Note, note_id)

    if note is None:
        return jsonify({"error": "note not found"}), 404

    # Authorisation — only the owner may edit their own notes.
    if note.user_id != user.id:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = data["title"].strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 422
        note.title = title

    if "content" in data:
        content = data["content"].strip()
        if not content:
            return jsonify({"error": "content cannot be empty"}), 422
        note.content = content

    db.session.commit()
    return jsonify(note.to_dict()), 200


# ---------------------------------------------------------------------------
# DELETE /notes/<id>
# ---------------------------------------------------------------------------

@notes_bp.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    """
    Delete a note.

    Only the owner of the note may delete it.
    Returns 204 No Content on success.
    """
    user, err = get_authenticated_user()
    if err:
        return err

    note = db.session.get(Note, note_id)

    if note is None:
        return jsonify({"error": "note not found"}), 404

    # Authorisation — only the owner may delete their own notes.
    if note.user_id != user.id:
        return jsonify({"error": "forbidden"}), 403

    db.session.delete(note)
    db.session.commit()

    return "", 204