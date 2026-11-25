from flask import Blueprint, g, jsonify, request

from src.controllers import pedido_controller
from src.middlewares.auth import login_required
from src.models.database import get_db

pedido_bp = Blueprint("pedidos", __name__)


@pedido_bp.route("/pedidos", methods=["POST"])
@login_required
def criar_pedido():
    resultado = pedido_controller.criar(get_db(), request.get_json(silent=True), g.usuario)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@pedido_bp.route("/pedidos", methods=["GET"])
def listar_todos_pedidos():
    return jsonify({"dados": pedido_controller.listar_todos(get_db()), "sucesso": True}), 200


@pedido_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_controller.listar_do_usuario(get_db(), usuario_id), "sucesso": True}), 200


@pedido_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
@login_required
def atualizar_status_pedido(pedido_id):
    pedido_controller.atualizar_status(get_db(), pedido_id, request.get_json(silent=True), g.usuario)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
