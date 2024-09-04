from app import db

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    created_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<Task {self.title}>'

class TaskList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    created_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<TaskList {self.title}>'