from flask import Blueprint, jsonify, request

from src.controllers import produto_controller
from src.middlewares.auth import admin_required
from src.models.database import get_db

produto_bp = Blueprint("produtos", __name__)


@produto_bp.route("/produtos", methods=["GET"])
def listar_produtos():
    return jsonify({"dados": produto_controller.listar(get_db()), "sucesso": True}), 200


@produto_bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    resultados = produto_controller.pesquisar(
        get_db(),
        termo=request.args.get("q", ""),
        categoria=request.args.get("categoria"),
        preco_min=request.args.get("preco_min"),
        preco_max=request.args.get("preco_max"),
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


@produto_bp.route("/produtos/<int:produto_id>", methods=["GET"])
def buscar_produto(produto_id):
    return jsonify({"dados": produto_controller.buscar(get_db(), produto_id), "sucesso": True}), 200


@produto_bp.route("/produtos", methods=["POST"])
@admin_required
def criar_produto():
    produto_id = produto_controller.criar(get_db(), request.get_json(silent=True))
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


@produto_bp.route("/produtos/<int:produto_id>", methods=["PUT"])
@admin_required
def atualizar_produto(produto_id):
    produto_controller.atualizar(get_db(), produto_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@produto_bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
@admin_required
def deletar_produto(produto_id):
    produto_controller.deletar(get_db(), produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
