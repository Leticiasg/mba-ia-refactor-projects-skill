from flask import Blueprint, current_app, jsonify, request

from src.controllers import admin_controller
from src.middlewares.auth import require_admin
from src.models.database import get_db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/reset-db", methods=["POST"])
@require_admin
def reset_database():
    admin_controller.resetar_banco(get_db())
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@admin_bp.route("/admin/query", methods=["POST"])
@require_admin
def executar_query():
    dados = admin_controller.executar_consulta(
        current_app.config["DATABASE_PATH"], request.get_json(silent=True) or {}
    )
    return jsonify({"dados": dados, "sucesso": True}), 200
