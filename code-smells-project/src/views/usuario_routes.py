from flask import Blueprint, jsonify, request

from src.controllers import usuario_controller
from src.models.database import get_db

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    return jsonify({"dados": usuario_controller.listar(get_db()), "sucesso": True}), 200


@usuario_bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    return jsonify({"dados": usuario_controller.buscar(get_db(), usuario_id), "sucesso": True}), 200


@usuario_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    usuario_id = usuario_controller.criar(get_db(), request.get_json(silent=True))
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


@usuario_bp.route("/login", methods=["POST"])
def login():
    usuario = usuario_controller.login(get_db(), request.get_json(silent=True) or {})
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
