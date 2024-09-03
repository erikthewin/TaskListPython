# init_db.py

from app import app, db
from models import Task
from sqlalchemy.exc import OperationalError

def is_db_initialized():
    # Check if any rows exist in the Task table
    try:
        return Task.query.first() is not None
    except OperationalError:
        # This will handle cases where the table doesn't even exist
        return False

# Create an application context
with app.app_context():
    if not is_db_initialized():
        # Initialize the database
        db.create_all()
        print("Database initialized.")
    else:
        print("Database already initialized, skipping.")
