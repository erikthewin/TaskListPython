# init_db.py

from app import app, db
from models import Task, List  # Import both models
from sqlalchemy.exc import OperationalError
from datetime import date, timedelta

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
        list3 = List(title="Work", description="Tasks for the office", created_date=date.today())
        list4 = List(title="Shopping", description="Things to buy", created_date=date.today())
        list5 = List(title="Fitness", description="Workout and health goals", created_date=date.today())
        list6 = List(title="Car Maintenance", description="Tasks related to the car", created_date=date.today())
        list7 = List(title="Hobbies", description="Things to do for fun", created_date=date.today())
        list8 = List(title="Travel", description="Trips and travel plans", created_date=date.today())
        list9 = List(title="Finances", description="Manage financial tasks", created_date=date.today())
        list10 = List(title="Health", description="Medical and health-related tasks", created_date=date.today())

        # Add the sample lists to the session
        db.session.add_all([list1, list2, list3, list4, list5, list6, list7, list8, list9, list10])
        db.session.commit()  # Commit the lists so they have IDs

        # Create sample data for Tasks
        tasks = [
            # Housework
            Task(title="Fix the floorboard in the kitchen", created_date=date.today(), due_date=date.today() + timedelta(days=7), status=False, list_id=list1.id),
            Task(title="Clean the windows", created_date=date.today() - timedelta(days=1), due_date=date.today() + timedelta(days=5), status=False, list_id=list1.id),
            Task(title="Paint the guestroom", created_date=date.today(), due_date=date.today() + timedelta(days=14), status=False, list_id=list1.id),
            Task(title="Vacuum the living room", created_date=date.today(), due_date=date.today() + timedelta(days=1), status=True, list_id=list1.id),
            Task(title="Clean the bathroom", created_date=date.today(), due_date=date.today() + timedelta(days=2), status=False, list_id=list1.id),
            
            # Gardenwork
            Task(title="Mow the lawn", created_date=date.today(), due_date=date.today() + timedelta(days=3), status=False, list_id=list2.id),
            Task(title="Water the plants", created_date=date.today(), due_date=date.today(), status=False, list_id=list2.id),
            Task(title="Buy potting soil", created_date=date.today(), due_date=date.today() + timedelta(days=3), status=False, list_id=list2.id),
            Task(title="Trim the hedges", created_date=date.today() - timedelta(days=2), due_date=date.today() + timedelta(days=2), status=False, list_id=list2.id),
            
            # Work
            Task(title="Submit quarterly report", created_date=date.today() - timedelta(days=1), due_date=date.today() + timedelta(days=10), status=False, list_id=list3.id),
            Task(title="Prepare presentation slides", created_date=date.today() - timedelta(days=3), due_date=date.today() + timedelta(days=4), status=True, list_id=list3.id),
            Task(title="Schedule team meeting", created_date=date.today(), due_date=date.today() + timedelta(days=1), status=True, list_id=list3.id),
            Task(title="Review project proposal", created_date=date.today(), due_date=date.today() + timedelta(days=2), status=False, list_id=list3.id),
            
            # Shopping
            Task(title="Buy groceries for the week", created_date=date.today(), due_date=date.today() + timedelta(days=2), status=False, list_id=list4.id),
            Task(title="Purchase birthday gift for Sarah", created_date=date.today() - timedelta(days=5), due_date=date.today() + timedelta(days=7), status=False, list_id=list4.id),
            Task(title="Order new office chair", created_date=date.today() - timedelta(days=3), due_date=date.today() + timedelta(days=4), status=False, list_id=list4.id),
            
            # Fitness
            Task(title="Go for a 5km run", created_date=date.today(), due_date=date.today() + timedelta(days=1), status=False, list_id=list5.id),
            Task(title="Buy new running shoes", created_date=date.today() - timedelta(days=2), due_date=date.today() + timedelta(days=5), status=False, list_id=list5.id),
            Task(title="Schedule yoga session", created_date=date.today() - timedelta(days=1), due_date=date.today() + timedelta(days=3), status=True, list_id=list5.id),
            
            # Car Maintenance
            Task(title="Change oil", created_date=date.today() - timedelta(days=1), due_date=date.today() + timedelta(days=30), status=False, list_id=list6.id),
            Task(title="Wash the car", created_date=date.today(), due_date=date.today() + timedelta(days=7), status=False, list_id=list6.id),
            Task(title="Check tire pressure", created_date=date.today(), due_date=date.today() + timedelta(days=2), status=True, list_id=list6.id),
            
            # Hobbies
            Task(title="Start new painting", created_date=date.today(), due_date=date.today() + timedelta(days=10), status=False, list_id=list7.id),
            Task(title="Finish reading 'The Great Gatsby'", created_date=date.today() - timedelta(days=7), due_date=date.today() + timedelta(days=3), status=False, list_id=list7.id),
            
            # Travel
            Task(title="Book flight to New York", created_date=date.today() - timedelta(days=2), due_date=date.today() + timedelta(days=5), status=True, list_id=list8.id),
            Task(title="Renew passport", created_date=date.today(), due_date=date.today() + timedelta(days=14), status=False, list_id=list8.id),
            
            # Finances
            Task(title="Pay credit card bill", created_date=date.today(), due_date=date.today() + timedelta(days=5), status=False, list_id=list9.id),
            Task(title="Review investment portfolio", created_date=date.today() - timedelta(days=1), due_date=date.today() + timedelta(days=10), status=False, list_id=list9.id),
            
            # Health
            Task(title="Schedule dentist appointment", created_date=date.today(), due_date=date.today() + timedelta(days=3), status=False, list_id=list10.id),
            Task(title="Pick up prescription", created_date=date.today(), due_date=date.today() + timedelta(days=2), status=False, list_id=list10.id),
            Task(title="Get annual physical", created_date=date.today() - timedelta(days=10), due_date=date.today() + timedelta(days=20), status=True, list_id=list10.id)
        ]

        # Add the sample tasks to the session
        db.session.add_all(tasks)

        # Commit the session to save everything to the database
        db.session.commit()

        print("Database initialized with sample data.")
    else:
        print("Database already initialized, skipping.")