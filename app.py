import logging
from flask import Flask, render_template, redirect, url_for, request, jsonify, abort, flash
from werkzeug.exceptions import HTTPException, NotFound, BadRequest
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__, static_folder='assets')
app.json.sort_keys = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')  # Secret key for flash sessions
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

ENABLE_FILE_LOGGING = os.environ.get('ENABLE_FILE_LOGGING')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')  # Default to info
IS_LOGGING_DEBUG = True if LOG_LEVEL.lower() == 'debug' else False

# Convert LOG_LEVEL string to the corresponding logging level constant
try:
    log_level_value = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
except AttributeError:
    raise ValueError(f"Unknown logging level: {LOG_LEVEL}")

LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=log_level_value, format=LOGGING_FORMAT)

logger = logging.getLogger('task_manager_app')

if ENABLE_FILE_LOGGING:
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(log_level_value)
    file_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    logger.addHandler(file_handler)
    logger.info("File logging is enabled with level: %s", logging.getLevelName(log_level_value))

from models import Task, List

# List functions

def get_all_lists():
    try:
        data = List.query.all()
        logger.debug("Fetched all lists")
        return data, 200
    except Exception as e:
        logger.error(f"Error getting lists: {str(e)}")
        return None, 500

def get_list_by_id(list_id):
    if not list_id:
        logger.warning("Bad request: missing list_id")
        return None, 400

    try:
        list = List.query.filter_by(id=list_id).first()
        if list is None:
            logger.info(f"List with id: {list_id} not found")
            return None, 404
        logger.debug(f"Fetched list {list.id} with title: {list.title}")
        return list, 200
    except Exception as e:
        logger.error(f"Error retrieving list {list_id}: {str(e)}")
        return None, 500

def create_list(data):
    if not data or 'title' not in data or 'description' not in data:
        logger.warning("Bad request: Missing title or description")
        return None, 400

    try:
        new_list = List(
            title=data['title'],
            description=data['description'],
            created_date=datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d').date()
        )
        db.session.add(new_list)
        db.session.commit()
        logger.debug(f"Created list with title: {new_list.title}")
        return new_list, 201
    except Exception as e:
        logger.error(f"Error creating list: {str(e)}")
        return None, 500

def update_list(list_item, data):
    if not data:
        logger.warning("Bad request: no data provided")
        return None, 400

    try:
        list_item.title = data.get('title', list_item.title)
        list_item.description = data.get('description', list_item.description)
        db.session.commit()
        logger.debug(f"Updated list {list_item.id}")
        return list_item, 200
    except Exception as e:
        logger.error(f"Error updating list {list_item.id}: {str(e)}")
        return None, 500

def delete_list(list_item):
    if not list_item:
        logger.warning("Bad request: list does not exist")
        return None, 400

    try:
        db.session.delete(list_item)
        db.session.commit()
        logger.debug(f"Deleted list {list_item.id}")
        return True, 200
    except Exception as e:
        logger.error(f"Error deleting list {list_item.id}: {str(e)}")
        return None, 500

# Task functions

def get_all_tasks():
    try:
        tasks = Task.query.all()
        logger.debug("Fetched all tasks")
        return tasks, 200
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}")
        return None, 500

def get_task_by_id(task_id):
    if not task_id:
        logger.warning("Bad request: missing task_id")
        return None, 400

    try:
        task = Task.query.filter_by(id=task_id).first()
        if task is None:
            logger.info(f"Task {task_id} not found")
            return None, 404
        return task, 200
    except Exception as e:
        logger.error(f"Error retrieving task {task_id}: {str(e)}")
        return None, 500

def create_task(data):
    if not data or 'title' not in data or 'due_date' not in data or 'list_id' not in data:
        logger.warning("Bad request: Missing required fields")
        return None, 400

    try:
        new_task = Task(
            title=data['title'],
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
            created_date=datetime.today().date(),
            list_id=data['list_id'],
            status=False
        )
        db.session.add(new_task)
        db.session.commit()
        logger.debug(f"Created task with title: {new_task.title}")
        return new_task, 201
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        return None, 500

def update_task(task, data):
    if not data:
        logger.warning("Bad request: no data provided")
        return None, 400

    try:
        task.title = data.get('title', task.title)
        if 'due_date' in data:
            task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        db.session.commit()
        logger.debug(f"Updated task {task.id}")
        return task, 200
    except Exception as e:
        logger.error(f"Error updating task {task.id}: {str(e)}")
        return None, 500

def complete_task(task):
    try:
        task.status = True
        db.session.commit()
        return task, 200
    except Exception as e:
        logger.error(f"Error completing task {task.id}: {str(e)}")
        return None, 500

def delete_task(task):
    if not task:
        logger.warning("Bad request: task does not exist")
        return None, 400

    try:
        db.session.delete(task)
        db.session.commit()
        logger.debug(f"Deleted task {task.id}")
        return True, 200
    except Exception as e:
        logger.error(f"Error deleting task {task.id}: {str(e)}")
        return None, 500
    
# Import export functions

def import_data_from_json(data):
    if not data or not isinstance(data, list):
        return None, 400

    list_insert_count = 0
    task_insert_count = 0

    try:
        for list_data in data:
            list_obj = List.query.filter_by(id=list_data.get('id')).first()
            if not list_obj:
                list_obj = List(
                    id=list_data['id'],
                    title=list_data['title'],
                    description=list_data['description'],
                    created_date=datetime.strptime(list_data['created_date'], '%Y-%m-%d').date()
                )
                db.session.add(list_obj)
                list_insert_count += 1

            db.session.commit()

            for task_data in list_data['tasks']:
                task_obj = Task.query.filter_by(id=task_data.get('id')).first()
                if not task_obj:
                    task_obj = Task(
                        id=task_data['id'],
                        title=task_data['title'],
                        status=task_data['status'],
                        due_date=datetime.strptime(task_data['due_date'], '%Y-%m-%d').date(),
                        created_date=datetime.strptime(task_data['created_date'], '%Y-%m-%d').date(),
                        list_id=list_obj.id
                    )
                    db.session.add(task_obj)
                    task_insert_count += 1

            db.session.commit()

        return {"lists_inserted": list_insert_count, "tasks_inserted": task_insert_count}, 200
    except Exception as e:
        logger.error(f"Error importing data: {str(e)}")
        return None, 500

def export_data_as_json():
    try:
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

        return data, 200
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return None, 500
    
# ROUTES

# Lists for webinterface

@app.route('/')
def index():
    lists, status_code = get_all_lists()
    if status_code == 200:
        return render_template('index.html', lists=lists)
    else:
        flash('Error fetching lists', 'error')
        return render_template('index.html')

@app.route('/add', methods=['GET', 'POST'])
def app_add_list():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        result, status_code = create_list({'title': title, 'description': description})
        if status_code == 201:
            flash('List created successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Error creating list', 'error')
    return render_template('add_list.html')

@app.route('/edit/<int:list_id>', methods=['GET', 'POST'])
def app_edit_list(list_id):
    list_item, status_code = get_list_by_id(list_id)
    if status_code != 200:
        flash('List not found', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        result, status_code = update_list(list_item, {'title': title, 'description': description})
        if status_code == 200:
            flash('List updated successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Error updating list', 'error')

    return render_template('edit_list.html', list=list_item)

@app.route('/delete/<int:list_id>', methods=['GET'])
def app_delete_list(list_id):
    list_item, status_code = get_list_by_id(list_id)
    if status_code != 200:
        flash('List not found', 'error')
        return redirect(url_for('index'))

    result, status_code = delete_list(list_item)
    if status_code == 200:
        flash('List deleted successfully', 'success')
    else:
        flash('Error deleting list', 'error')

    return redirect(url_for('index'))

# Tasks for webinterface

@app.route('/lists/<int:list_id>/tasks')
def tasks_index(list_id):
    list_item, status_code = get_list_by_id(list_id)
    if status_code != 200:
        flash('List not found', 'error')
        return redirect(url_for('index'))

    tasks, status_code = get_all_tasks()
    if status_code != 200:
        flash('Error fetching tasks', 'error')
        return render_template('tasks/index.html', list=list_item, tasks=[])

    return render_template('tasks/index.html', list=list_item, tasks=tasks)

@app.route('/lists/<int:list_id>/tasks/add', methods=['GET', 'POST'])
def app_add_task(list_id):
    list_item, status_code = get_list_by_id(list_id)
    if status_code != 200:
        flash('List not found', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        due_date = request.form['due_date']
        result, status_code = create_task({'title': title, 'due_date': due_date, 'list_id': list_item.id})
        if status_code == 201:
            flash('Task created successfully', 'success')
            return redirect(url_for('tasks_index', list_id=list_item.id))
        else:
            flash('Error creating task', 'error')

    return render_template('tasks/add_task.html', list=list_item)

@app.route('/list/<int:list_id>/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
def app_edit_task(list_id, task_id):
    task, status_code = get_task_by_id(task_id)
    if status_code != 200:
        flash('Task not found', 'error')
        return redirect(url_for('tasks_index', list_id=list_id))

    list_item, status_code = get_list_by_id(list_id)
    if status_code != 200:
        flash('List not found', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        due_date = request.form['due_date']
        result, status_code = update_task(task, {'title': title, 'due_date': due_date})
        if status_code == 200:
            flash('Task updated successfully', 'success')
            return redirect(url_for('tasks_index', list_id=list_id))
        else:
            flash('Error updating task', 'error')

    return render_template('tasks/edit_task.html', task=task, list=list_item)

@app.route('/list/<int:list_id>/tasks/<int:task_id>/complete', methods=['GET'])
def app_complete_task(list_id, task_id):
    task, status_code = get_task_by_id(task_id)
    if status_code != 200:
        flash('Task not found', 'error')
        return redirect(url_for('tasks_index', list_id=list_id))

    result, status_code = complete_task(task)
    if status_code == 200:
        flash(f'Task {task.title} completed successfully', 'success')
    else:
        flash('Error completing task', 'error')

    return redirect(url_for('tasks_index', list_id=list_id))

@app.route('/list/<int:list_id>/tasks/delete/<int:task_id>', methods=['GET'])
def app_delete_task(list_id, task_id):
    task, status_code = get_task_by_id(task_id)
    if status_code != 200:
        flash('Task not found', 'error')
        return redirect(url_for('tasks_index', list_id=list_id))

    result, status_code = delete_task(task)
    if status_code == 200:
        flash('Task deleted successfully', 'success')
    else:
        flash('Error deleting task', 'error')

    return redirect(url_for('tasks_index', list_id=list_id))

# Backup for webinterface

@app.route('/backup', methods=['GET', 'POST'])
def backup():
    # Implement backup functionality here, if needed
    return render_template('backup.html')

# List for API

@app.route('/api/lists', methods=['GET'])
def api_get_lists():
    try:
        lists, status_code = get_all_lists()
        if status_code == 200:
            lists_list = [{'id': list.id, 'title': list.title, 'description': list.description, 'created_date': list.created_date.strftime('%Y-%m-%d')} for list in lists]
            return jsonify(lists_list), 200
        else:
            return '', status_code
    except Exception:
        return '', 500

@app.route('/api/lists/<int:list_id>', methods=['GET'])
def api_get_list(list_id):
    try:
        list_item, status_code = get_list_by_id(list_id)
        if status_code == 200:
            list_data = {'id': list_item.id, 'title': list_item.title, 'description': list_item.description, 'created_date': list_item.created_date.strftime('%Y-%m-%d')}
            return jsonify(list_data), 200
        else:
            return '', status_code
    except Exception:
        return '', 500

@app.route('/api/lists', methods=['POST'])
def api_post_list():
    try:
        data = request.get_json()
        new_list, status_code = create_list(data)
        if status_code == 201:
            return jsonify({'id': new_list.id, 'title': new_list.title, 'description': new_list.description, 'created_date': new_list.created_date.strftime('%Y-%m-%d')}), 201
        else:
            return '', status_code
    except Exception:
        return '', 500

@app.route('/api/lists/<int:list_id>', methods=['PUT'])
def api_put_list(list_id):
    try:
        list_item, status_code = get_list_by_id(list_id)
        if status_code != 200:
            return '', status_code

        data = request.get_json()
        updated_list, status_code = update_list(list_item, data)
        if status_code == 200:
            return jsonify({'id': updated_list.id, 'title': updated_list.title, 'description': updated_list.description, 'created_date': updated_list.created_date.strftime('%Y-%m-%d')}), 200
        else:
            return '', status_code
    except Exception:
        return '', 500

@app.route('/api/lists/<int:list_id>', methods=['DELETE'])
def api_delete_list(list_id):
    try:
        list_item, status_code = get_list_by_id(list_id)
        if status_code != 200:
            return '', status_code

        status_code = delete_list(list_item)
        return '', status_code
    except Exception:
        return '', 500

# Tasks for API

@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    try:
        tasks, status_code = get_all_tasks()
        if status_code == 200:
            tasks_list = [{'id': task.id, 'list_id': task.list_id, 'title': task.title, 'status': task.status, 'due_date': task.due_date.strftime('%Y-%m-%d'), 'created_date': task.created_date.strftime('%Y-%m-%d')} for task in tasks]
            return jsonify(tasks_list), 200
        else:
            return '', status_code
    except Exception:
        return '', 500

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def api_get_task(task_id):
    try:
        task, status_code = get_task_by_id(task_id)
        if status_code == 200:
            task_data = {'id': task.id, 'title': task.title, 'status': task.status, 'due_date': task.due_date.strftime('%Y-%m-%d'), 'created_date': task.created_date.strftime('%Y-%m-%d')}
            return jsonify(task_data), 200
        else:
            return '', status_code
    except Exception:
        return '', 500

@app.route('/api/tasks', methods=['POST'])
def api_post_task():
    try:
        data = request.get_json()
        new_task, status_code = create_task(data)
        if status_code == 201:
            return jsonify({'id': new_task.id, 'title': new_task.title, 'status': new_task.status, 'due_date': new_task.due_date.strftime('%Y-%m-%d'), 'created_date': new_task.created_date.strftime('%Y-%m-%d')}), 201
        else:
            return '', status_code
    except Exception:
        return '', 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def api_put_task(task_id):
    try:
        task, status_code = get_task_by_id(task_id)
        if status_code != 200:
            return '', status_code

        data = request.get_json()
        updated_task, status_code = update_task(task, data)
        if status_code == 200:
            return jsonify({'id': updated_task.id, 'title': updated_task.title, 'status': updated_task.status, 'due_date': updated_task.due_date.strftime('%Y-%m-%d'), 'created_date': updated_task.created_date.strftime('%Y-%m-%d')}), 200
        else:
            return '', status_code
    except Exception:
        return '', 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    try:
        task, status_code = get_task_by_id(task_id)
        if status_code != 200:
            return '', status_code

        status_code = delete_task(task)
        return '', status_code
    except Exception:
        return '', 500

# Import & Export for API

@app.route('/api/import', methods=['POST'])
def api_import_data():
    try:
        data = request.get_json()
        result = import_data_from_json(data)
        return '', 201
    except Exception:
        return '', 500

@app.route('/api/export', methods=['GET'])
def api_export_data():
    try:
        data = export_data_as_json()
        return jsonify(data), 200
    except Exception:
        return '', 500

if __name__ == '__main__':
    app.run(debug=IS_LOGGING_DEBUG)