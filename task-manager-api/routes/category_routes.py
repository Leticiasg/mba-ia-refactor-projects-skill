from flask import Blueprint, jsonify, request

from controllers import category_controller
from middlewares.auth import current_user, require_auth

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(category_controller.list_categories()), 200


@category_bp.route('/categories', methods=['POST'])
def create_category():
    return jsonify(category_controller.create_category(request.get_json(silent=True))), 201


@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    category = category_controller.update_category(category_id, request.get_json(silent=True))
    return jsonify(category), 200


@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@require_auth
def delete_category(category_id):
    category_controller.delete_category(category_id, current_user())
    return jsonify({'message': 'Categoria deletada'}), 200
