from flask import Blueprint, g, jsonify, request

from controllers import category_controller
from middlewares.auth import login_required

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(category_controller.list_categories()), 200


@category_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    category = category_controller.create_category(request.get_json(silent=True), g.current_user)
    return jsonify(category), 201


@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    category = category_controller.update_category(category_id, request.get_json(silent=True), g.current_user)
    return jsonify(category), 200


@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    category_controller.delete_category(category_id, g.current_user)
    return jsonify({'message': 'Categoria deletada'}), 200
