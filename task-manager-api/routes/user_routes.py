from flask import Blueprint, g, jsonify, request

from controllers import user_controller
from middlewares.auth import login_required, optional_auth

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(user_controller.list_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify(user_controller.get_user(user_id)), 200


@user_bp.route('/users', methods=['POST'])
@optional_auth
def create_user():
    user = user_controller.create_user(request.get_json(silent=True), g.current_user)
    return jsonify(user), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    user = user_controller.update_user(user_id, request.get_json(silent=True), g.current_user)
    return jsonify(user), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    user_controller.delete_user(user_id, g.current_user)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    return jsonify(user_controller.get_user_tasks(user_id)), 200


@user_bp.route('/login', methods=['POST'])
def login():
    return jsonify(user_controller.login(request.get_json(silent=True))), 200
