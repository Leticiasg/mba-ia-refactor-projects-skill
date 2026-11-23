from flask import Blueprint, jsonify, request

from controllers import user_controller
from middlewares.auth import generate_token, get_authenticated_user, require_admin
from models.database import utcnow

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    result = []
    for user, task_count, _done in user_controller.list_users():
        user_data = user.to_dict()
        user_data['task_count'] = task_count
        result.append(user_data)
    return jsonify(result), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user, tasks = user_controller.get_user_with_tasks(user_id)
    user_data = user.to_dict()
    user_data['tasks'] = [task.to_dict() for task in tasks]
    return jsonify(user_data), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    user = user_controller.create_user(request.get_json(silent=True), get_authenticated_user())
    return jsonify(user.to_dict()), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = user_controller.update_user(user_id, request.get_json(silent=True), get_authenticated_user())
    return jsonify(user.to_dict()), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    user_controller.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    _user, tasks = user_controller.get_user_with_tasks(user_id)
    now = utcnow()
    return jsonify([task.to_user_task_dict(now) for task in tasks]), 200


@user_bp.route('/login', methods=['POST'])
def login():
    user = user_controller.authenticate(request.get_json(silent=True))
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': generate_token(user),
    }), 200
