from flask import Flask, render_template, redirect, url_for, request, jsonify, abort, flash
from flask_sqlalchemy import SQLAlchemy
from forms import TaskForm, ListForm
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

from models import Task, List

def get_all_lists():
    return List.query.all()

def get_list_by_id(list_id):
    list = List.query.get(list_id)
    if not list:
        abort(404)
    return list

def create_list(data):
    if not data or not 'title' in data or not 'description' in data:
        abort(400, description="Bad request, title and description are required")
    new_list = List(title=data['title'], description=data['description'], created_date=datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d').date())
    db.session.add(new_list)
    db.session.commit()
    return new_list

def update_list(list, data):
    if not data:
        abort(400, description="Bad request, data is required")
    
    list.title = data.get('title', list.title)
    if 'description' in data:
        list.description = data.get('description', list.description)
    
    db.session.commit()
    return list

def delete_list(list):
    try:
        db.session.delete(list)
        db.session.commit()
        return True
    except:
        return False

def get_all_tasks():
    return Task.query.all()

def get_task_by_id(task_id):
    task = Task.query.get(task_id)
    if not task:
        abort(404)
    return task

def create_task(data):
    if not data or not 'title' in data or not 'due_date' in data or not 'list_id' in data:
        abort(400, description="Bad request, title, due_date, and list_id are required")

    new_task = Task(
        title=data['title'],
        due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
        created_date=datetime.today().date(),
        list_id=data['list_id'],
        status=False
    )
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

# Web interface routes for lists

@app.route('/')
def index():
    lists = get_all_lists()
    return render_template('index.html', lists=lists)

@app.route('/add', methods=['GET', 'POST'])
def app_add_list():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        create_list({'title': title, 'description': description})
        return redirect(url_for('index'))
    return render_template('add_list.html')

@app.route('/edit/<int:list_id>', methods=['GET', 'POST'])
def app_edit_list(list_id):
    list = get_list_by_id(list_id)
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        update_list(list, {'title': title, 'description': description})
        return redirect(url_for('index'))
    return render_template('edit_list.html', list=list)

@app.route('/delete/<int:list_id>', methods=['GET'])
def app_delete_list(list_id):
    list = get_list_by_id(list_id)
    if (delete_list(list)):
        flash('List deleted', 'success')
    else:
        flash('List could not be deleted', 'error')
    return redirect(url_for('index'))

# Web interface routes for tasks

@app.route('/lists/<int:list_id>/tasks')
def tasks_index(list_id):
    list = get_list_by_id(list_id)
    tasks = list.tasks
    return render_template('tasks/index.html', list=list, tasks=tasks)

@app.route('/lists/<int:list_id>/tasks/add', methods=['GET', 'POST'])
def app_add_task(list_id):
    list = get_list_by_id(list_id)
    if request.method == 'POST':
        title = request.form['title']
        due_date = request.form['due_date']
        create_task({'title': title, 'due_date': due_date, 'list_id': list.id})
        return redirect(url_for('tasks_index', list_id=list.id))
    return render_template('tasks/add_task.html', list=list)

@app.route('/list/<int:list_id>/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
def app_edit_task(list_id, task_id):
    task = get_task_by_id(task_id)
    list = get_list_by_id(list_id)
    if request.method == 'POST':
        title = request.form['title']
        due_date = request.form['due_date']
        update_task(task, {'title': title, 'due_date': due_date})
        return redirect(url_for('tasks_index', list_id=list_id))
    return render_template('tasks/edit_task.html', task=task, list=list)

@app.route('/list/<int:list_id>/tasks/delete/<int:task_id>', methods=['GET'])
def app_delete_task(list_id, task_id):
    task = get_task_by_id(task_id)
    delete_task(task)
    return redirect(url_for('tasks_index', list_id=list_id))

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

@app.route('/api/backup', methods=['GET'])
def api_backup():
    task = get_all_tasks()

if __name__ == '__main__':
    app.run(debug=True)