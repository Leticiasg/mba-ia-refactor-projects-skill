from flask import Blueprint, current_app, g, jsonify, request

from controllers import task_controller
from middlewares.auth import login_required

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(task_controller.list_tasks()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(task_controller.get_task(task_id)), 200


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    notifier = current_app.extensions['notification_service']
    task = task_controller.create_task(request.get_json(silent=True), g.current_user, notifier)
    return jsonify(task), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = task_controller.update_task(task_id, request.get_json(silent=True), g.current_user)
    return jsonify(task), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task_controller.delete_task(task_id, g.current_user)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    tasks = task_controller.search_tasks(
        text=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )
    return jsonify(tasks), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_controller.get_stats()), 200
