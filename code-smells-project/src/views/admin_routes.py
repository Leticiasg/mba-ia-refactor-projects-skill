import logging
import sqlite3

from flask import Blueprint, current_app, jsonify, request

from src.controllers import admin_controller
from src.middlewares.auth import require_admin
from src.models.database import get_db

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/", methods=["GET"])
def index():
    return jsonify(admin_controller.boas_vindas())


@admin_bp.route("/health", methods=["GET"])
def health_check():
    try:
        status = admin_controller.status_sistema(get_db(), current_app.config["APP_ENV"])
    except sqlite3.Error:
        logger.exception("Health check falhou ao acessar o banco")
        return jsonify({"status": "erro", "detalhes": "Banco de dados indisponível"}), 500
    return jsonify(status), 200


@admin_bp.route("/admin/reset-db", methods=["POST"])
@require_admin
def reset_database():
    admin_controller.resetar_banco(get_db())
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@admin_bp.route("/admin/query", methods=["POST"])
@require_admin
def executar_query():
    dados = admin_controller.executar_consulta(current_app.config["DATABASE_PATH"], request.get_json(silent=True))
    return jsonify({"dados": dados, "sucesso": True}), 200
