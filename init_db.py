# init_db.py

from app import app, db
from models import Task, List  # Import both models
from sqlalchemy.exc import OperationalError
from datetime import date

def is_db_initialized():
    # Check if any rows exist in the List table
    try:
        return List.query.first() is not None
    except OperationalError:
        # This will handle cases where the table doesn't even exist
        return False

# Create an application context
with app.app_context():
    if not is_db_initialized():
        # Initialize the database
        db.create_all()

        # Create sample data for Lists
        list1 = List(title="Housework", description="Stuff to do around the house", created_date=date.today())
        list2 = List(title="Gardenwork", description="Duties in the garden", created_date=date.today())

        # Add the sample lists to the session
        db.session.add(list1)
        db.session.add(list2)
        db.session.commit()  # Commit the lists so they have IDs

        # Create sample data for Tasks
        task1 = Task(title="Fix the floorboard in the kitchen", created_date=date.today(), due_date=date.today(), status=False, list_id=list1.id)
        task2 = Task(title="Mow the lawn", created_date=date.today(), due_date=date.today(), status=False, list_id=list2.id)
        task3 = Task(title="Paint the guestroom", created_date=date.today(), due_date=date.today(), status=False, list_id=list1.id)

        # Add the sample tasks to the session
        db.session.add(task1)
        db.session.add(task2)
        db.session.add(task3)

        # Commit the session to save everything to the database
        db.session.commit()

        print("Database initialized with sample data.")
    else:
        print("Database already initialized, skipping.")