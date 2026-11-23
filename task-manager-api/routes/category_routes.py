from flask import Blueprint, jsonify, request

from controllers import category_controller

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    result = []
    for category, task_count in category_controller.list_categories():
        category_data = category.to_dict()
        category_data['task_count'] = task_count
        result.append(category_data)
    return jsonify(result), 200


@category_bp.route('/categories', methods=['POST'])
def create_category():
    category = category_controller.create_category(request.get_json(silent=True))
    return jsonify(category.to_dict()), 201


@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    category = category_controller.update_category(category_id, request.get_json(silent=True))
    return jsonify(category.to_dict()), 200


@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category_controller.delete_category(category_id)
    return jsonify({'message': 'Categoria deletada'}), 200
