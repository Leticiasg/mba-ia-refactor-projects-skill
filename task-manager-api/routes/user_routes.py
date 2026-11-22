from flask import Blueprint, jsonify, request

from controllers import user_controller
from middlewares.auth import get_current_user, issue_token

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
def get_users():
    return jsonify(user_controller.list_users()), 200


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return jsonify(user_controller.get_user(user_id)), 200


@user_bp.route("/users", methods=["POST"])
def create_user():
    user = user_controller.create_user(request.get_json(), actor=get_current_user())
    return jsonify(user), 201


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = user_controller.update_user(user_id, request.get_json(), actor=get_current_user())
    return jsonify(user), 200


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user_controller.delete_user(user_id)
    return jsonify({"message": "Usuário deletado com sucesso"}), 200


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id):
    return jsonify(user_controller.list_user_tasks(user_id)), 200


@user_bp.route("/login", methods=["POST"])
def login():
    user = user_controller.authenticate(request.get_json())
    return jsonify({
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
        "token": issue_token(user),
    }), 200
