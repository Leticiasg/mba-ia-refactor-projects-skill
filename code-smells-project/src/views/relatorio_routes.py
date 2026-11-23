from flask import Blueprint, jsonify

from src.controllers import relatorio_controller
from src.models.database import get_db

relatorio_bp = Blueprint("relatorios", __name__)


@relatorio_bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    return jsonify({"dados": relatorio_controller.vendas(get_db()), "sucesso": True}), 200
