from flask import Flask, render_template, redirect, url_for, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from forms import TaskForm
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

from models import Task

def get_all_tasks():
    return Task.query.all()

def get_task_by_id(task_id):
    task = Task.query.get(task_id)
    if not task:
        abort(404)
    return task

def create_task(data):
    if not data or not 'title' in data or not 'due_date' in data:
        abort(400, description="Bad request, title and due_date are required")
    
    new_task = Task(title=data['title'], due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date())
    db.session.add(new_task)
    db.session.commit()
    return new_task

def update_task(task, data):
    if not data:
        abort(400, description="Bad request, data is required")
    
    task.title = data.get('title', task.title)
    if 'due_date' in data:
        task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
    
    db.session.commit()
    return task

def delete_task(task):
    db.session.delete(task)
    db.session.commit()
    return True

# Web interface routes
@app.route('/')
def index():
    tasks = get_all_tasks()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['GET', 'POST'])
def app_add_task():
    if request.method == 'POST':
        title = request.form['title']
        due_date = request.form['due_date']
        create_task({'title': title, 'due_date': due_date})
        return redirect(url_for('index'))
    return render_template('add_task.html')

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def app_edit_task(task_id):
    task = get_task_by_id(task_id)
    if request.method == 'POST':
        title = request.form['title']
        due_date = request.form['due_date']
        update_task(task, {'title': title, 'due_date': due_date})
        return redirect(url_for('index'))
    return render_template('edit_task.html', task=task)

@app.route('/delete/<int:task_id>', methods=['GET'])
def app_delete_task(task_id):
    task = get_task_by_id(task_id)
    delete_task(task)
    return redirect(url_for('index'))

# REST API Endpoints
@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    tasks = get_all_tasks()
    tasks_list = [{'id': task.id, 'title': task.title, 'due_date': task.due_date.strftime('%Y-%m-%d')} for task in tasks]
    return jsonify(tasks_list)

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def api_get_task(task_id):
    task = get_task_by_id(task_id)
    task_data = {'id': task.id, 'title': task.title, 'due_date': task.due_date.strftime('%Y-%m-%d')}
    return jsonify(task_data)

@app.route('/api/tasks', methods=['POST'])
def api_post_task():
    data = request.get_json()
    new_task = create_task(data)
    return jsonify({'id': new_task.id, 'title': new_task.title, 'due_date': new_task.due_date.strftime('%Y-%m-%d')}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def api_put_task(task_id):
    task = get_task_by_id(task_id)
    data = request.get_json()
    updated_task = update_task(task, data)
    return jsonify({'id': updated_task.id, 'title': updated_task.title, 'due_date': updated_task.due_date.strftime('%Y-%m-%d')}), 200

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    task = get_task_by_id(task_id)
    delete_task(task)
    return jsonify({'message': 'Task deleted'}), 200

if __name__ == '__main__':
    app.run(debug=True)
