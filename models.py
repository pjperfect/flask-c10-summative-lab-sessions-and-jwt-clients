"""
Database models.

User  — stores account credentials; passwords are hashed with bcrypt.
Note  — a text note that belongs to exactly one User (user_id FK).
"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    """
    Represents an application user.

    Columns
    -------
    id          : integer primary key
    username    : unique string, used as the login identifier
    _password   : bcrypt hash stored in the db (never expose the raw value)
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    _password_hash = db.Column("password", db.String(200), nullable=False)

    # A user can own many notes; deleting the user cascades to their notes.
    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")

    # ------------------------------------------------------------------
    # Password helpers
    # ------------------------------------------------------------------

    @property
    def password(self):
        """Prevent accidental reads of the hash."""
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, plaintext: str):
        """Hash and store a new password."""
        self._password_hash = bcrypt.generate_password_hash(plaintext).decode("utf-8")

    def check_password(self, plaintext: str) -> bool:
        """Return True if *plaintext* matches the stored hash."""
        return bcrypt.check_password_hash(self._password_hash, plaintext)

    def to_dict(self) -> dict:
        return {"id": self.id, "username": self.username}

    def __repr__(self):
        return f"<User id={self.id} username={self.username!r}>"


class Note(db.Model):
    """
    Represents a personal note owned by a User.

    Columns
    -------
    id         : integer primary key
    title      : short heading for the note (max 120 chars)
    content    : full body text of the note
    user_id    : FK → users.id  (the owner)
    """

    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User", back_populates="notes")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "user_id": self.user_id,
        }

    def __repr__(self):
        return f"<Note id={self.id} title={self.title!r} user_id={self.user_id}>"