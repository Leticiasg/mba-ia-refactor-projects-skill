from flask import Blueprint, g, jsonify, request

from src.controllers import admin_controller
from src.middlewares.auth import admin_required
from src.models.database import get_db, get_readonly_db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/reset-db", methods=["POST"])
@admin_required
def reset_database():
    admin_controller.resetar_banco(get_db(), g.usuario)
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@admin_bp.route("/admin/query", methods=["POST"])
@admin_required
def executar_query():
    dados = admin_controller.executar_consulta(get_readonly_db(), request.get_json(silent=True))
    return jsonify({"dados": dados, "sucesso": True}), 200
