from flask import Blueprint, current_app, jsonify

from src.controllers import sistema_controller
from src.models.database import get_db

sistema_bp = Blueprint("sistema", __name__)


@sistema_bp.route("/", methods=["GET"])
def index():
    return jsonify(sistema_controller.boas_vindas())


@sistema_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify(sistema_controller.health(get_db(), current_app.config["AMBIENTE"])), 200
