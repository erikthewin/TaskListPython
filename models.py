from app import db

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    created_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Boolean, default=False, nullable=False) 
    due_date = db.Column(db.Date, nullable=False)
    
    # Foreign key to the List model
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=False)

    # Relationship to the List model
    list = db.relationship('List', back_populates='tasks')

    def __repr__(self):
        return f'<Task {self.title}>'

class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    created_date = db.Column(db.Date, nullable=False)

    # Relationship to the Task model
    tasks = db.relationship('Task', back_populates='list', lazy='dynamic')

    @property
    def task_count(self):
        return self.tasks.count()

    def __repr__(self):
        return f'<List {self.title}>'