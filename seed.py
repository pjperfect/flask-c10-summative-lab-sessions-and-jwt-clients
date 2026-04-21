"""
Seed script — populates the database with sample data for development.

Usage (from the project root, with the venv active):
    python seed.py

The script is idempotent: it clears existing data before inserting new rows
so it can be re-run safely during development.
"""

from faker import Faker
from app import app
from models import db, User, Note

fake = Faker()

# Number of demo users and notes per user to generate.
NUM_USERS = 5
NOTES_PER_USER = 8


def seed():
    with app.app_context():
        print("Clearing existing data …")
        # Delete in child-first order to respect FK constraints.
        Note.query.delete()
        User.query.delete()
        db.session.commit()

        print(f"Creating {NUM_USERS} users …")
        users = []
        for _ in range(NUM_USERS):
            # Ensure unique usernames within the seed batch.
            username = fake.unique.user_name()
            user = User(username=username)
            user.password = "password123"  # shared demo password
            db.session.add(user)
            users.append(user)

        db.session.commit()  # flush so user IDs are assigned

        print(f"Creating {NOTES_PER_USER} notes per user …")
        for user in users:
            for _ in range(NOTES_PER_USER):
                note = Note(
                    title=fake.sentence(nb_words=5).rstrip("."),
                    content=fake.paragraph(nb_sentences=4),
                    user_id=user.id,
                )
                db.session.add(note)

        db.session.commit()

        total_notes = NUM_USERS * NOTES_PER_USER
        print(f"Seeded {NUM_USERS} users and {total_notes} notes.")
        print("\nCredentials (any of the seeded users):")
        for u in users:
            print(f"   username: {u.username}   password: password123")


if __name__ == "__main__":
    seed()