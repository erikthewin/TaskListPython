from flask import Flask, render_template, redirect, url_for, request, jsonify, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__, static_folder='assets')
app.json.sort_keys = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key') # Secret key for flash sessions and other stuff
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

# Allow CORS only from a specific domain (e.g., localhost:3000)
CORS(app)

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

def get_tasks_by_list_id(list_id):
    try: 
        tasks = Task.query.filter_by(list_id=list_id).all()
        return tasks
    except:
        return None

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

def complete_task(task):
    task.status = True
    db.session.commit()
    return task

def delete_task(task):
    db.session.delete(task)
    db.session.commit()
    return True

def import_data_from_json(data):
    if not data or not isinstance(data, list):
        abort(400, description="Bad request, expected a list of lists with tasks.")

    list_insert_count = 0
    task_insert_count = 0

    for list_data in data:
        # Check if the list already exists
        list_obj = List.query.filter_by(id=list_data.get('id')).first()
        if not list_obj:
            # Create a new list
            list_obj = List(
                id=list_data['id'],
                title=list_data['title'],
                description=list_data['description'],
                created_date=datetime.strptime(list_data['created_date'], '%Y-%m-%d').date()
            )
            db.session.add(list_obj)
            list_insert_count += 1  # Increment list insert counter

        db.session.commit()

        # Process tasks within the list
        for task_data in list_data['tasks']:
            task_obj = Task.query.filter_by(id=task_data.get('id')).first()
            if not task_obj:
                # Create a new task
                task_obj = Task(
                    id=task_data['id'],
                    title=task_data['title'],
                    status=task_data['status'],
                    due_date=datetime.strptime(task_data['due_date'], '%Y-%m-%d').date(),
                    created_date=datetime.strptime(task_data['created_date'], '%Y-%m-%d').date(),
                    list_id=list_obj.id
                )
                db.session.add(task_obj)
                task_insert_count += 1  # Increment task insert counter

            db.session.commit()

    return {"lists_inserted": list_insert_count, "tasks_inserted": task_insert_count}

def export_data_as_json():
    lists = List.query.all()
    data = []

    for list in lists:
        tasks = Task.query.filter_by(list_id=list.id).all()
        task_data = [{'id': task.id, 'title': task.title, 'status': task.status, 'due_date': task.due_date.strftime('%Y-%m-%d'), 'created_date': task.created_date.strftime('%Y-%m-%d')} for task in tasks]

        list_data = {
            'id': list.id,
            'title': list.title,
            'description': list.description,
            'created_date': list.created_date.strftime('%Y-%m-%d'),
            'tasks': task_data
        }
        data.append(list_data)

    return data

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

@app.route('/list/<int:list_id>/tasks/<int:task_id>/complete', methods=['GET'])
def app_complete_task(list_id, task_id):
    task = get_task_by_id(task_id)
    if (complete_task(task)):
        flash(f'Task {task.title} completed', 'success')
    else:
        flash('Something went wrong', 'error')
    return redirect(url_for('tasks_index', list_id=list_id))
        

@app.route('/list/<int:list_id>/tasks/delete/<int:task_id>', methods=['GET'])
def app_delete_task(list_id, task_id):
    task = get_task_by_id(task_id)
    delete_task(task)
    return redirect(url_for('tasks_index', list_id=list_id))

# Web Interface route for backup

@app.route('/backup', methods=['GET', 'POST'])
def backup():
    return render_template('backup.html')

# REST API Endpoints for lists
@app.route('/api/lists', methods=['GET'])
def api_get_lists():
    lists = get_all_lists()
    lists_list = [{'id': list.id, 'title': list.title, 'description': list.description, 'created_date': list.created_date} for list in lists]
    return jsonify(lists_list), 200

@app.route('/api/lists/<int:list_id>', methods=['GET'])
def api_get_list(list_id):
    list = get_list_by_id(list_id)
    list_data = {'id': list.id, 'title': list.title, 'description': list.description, 'created_date': list.created_date.strftime('%Y-%m-%d')}
    return jsonify(list_data), 200

@app.route('/api/lists', methods=['POST'])
def api_post_list():
    data = request.get_json()
    new_list = create_list(data)
    return jsonify({'id': new_list.id, 'title': new_list.title, 'description': new_list.description, 'created_date': new_list.created_date.strftime('%Y-%m-%d')}), 201

@app.route('/api/lists/<int:list_id>', methods=['PUT'])
def api_put_list(list_id):
    list = get_list_by_id(list_id)
    data = request.get_json()
    updated_list = update_list(list, data)
    return jsonify({'id': updated_list.id, 'title': updated_list.title, 'description': updated_list.description, 'created_date': updated_list.created_date.strftime('%Y-%m-%d')}), 200

@app.route('/api/lists/<int:list_id>', methods=['DELETE'])
def api_delete_list(list_id):
    list = get_list_by_id(list_id)
    delete_list(list)
    return jsonify(""), 204

# REST API Endpoints for tasks
@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    tasks = get_all_tasks()
    tasks_list = [{'id': task.id, 'title': task.title, 'due_date': task.due_date.strftime('%Y-%m-%d')} for task in tasks]
    return jsonify(tasks_list)

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def api_get_task(task_id):
    task = get_task_by_id(task_id)
    task_data = {'id': task.id, 'title': task.title, 'status': task.status, 'due_date': task.due_date.strftime('%Y-%m-%d'), 'created_date': task.created_date.strftime('%Y-%m-%d')}
    if(task_data):
        return jsonify(task_data), 200
    else:
        return abort(204)

@app.route('/api/tasks', methods=['POST'])
def api_post_task():
    data = request.get_json()
    new_task = create_task(data)
    return jsonify({'id': new_task.id, 'title': new_task.title, 'status': new_task.status, 'due_date': new_task.due_date.strftime('%Y-%m-%d'), 'created_date': new_task.created_date.strftime('%Y-%m-%d')}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def api_put_task(task_id):
    task = get_task_by_id(task_id)
    data = request.get_json()
    updated_task = update_task(task, data)
    return jsonify({'id': updated_task.id, 'title': updated_task.title, 'status': updated_task.status, 'due_date': updated_task.due_date.strftime('%Y-%m-%d'), 'created_date': updated_task.created_date.strftime('%Y-%m-%d')}), 200

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    task = get_task_by_id(task_id)
    delete_task(task)
    return jsonify(""), 204

@app.route('/api/import', methods=['POST'])
def api_import_data():
    data = request.get_json()
    result = import_data_from_json(data)
    return jsonify({
        "message": "Data imported successfully!",
        "lists_inserted": result["lists_inserted"],
        "tasks_inserted": result["tasks_inserted"]
    }), 201

@app.route('/api/export', methods=['GET'])
def api_export_data():
    data = export_data_as_json()
    return jsonify(data), 200

if __name__ == '__main__':
    app.run(debug=True)