import logging

from src.config.settings import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PEDIDO_VALIDOS, STATUS_PENDENTE
from src.middlewares.errors import NotFoundError, ValidationError
from src.models import pedido_model, produto_model
from src.services import notification_service

logger = logging.getLogger(__name__)


def _eh_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _validar_itens(itens):
    if not isinstance(itens, list):
        raise ValidationError("Itens do pedido inválidos")
    for item in itens:
        if not isinstance(item, dict) or not _eh_inteiro(item.get("produto_id")) \
                or not _eh_inteiro(item.get("quantidade")) or item["quantidade"] <= 0:
            raise ValidationError("Item de pedido inválido: informe produto_id e quantidade maior que zero")


def criar(db, dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    _validar_itens(itens)

    produtos = {}
    total = 0
    for item in itens:
        produto_id = item["produto_id"]
        if produto_id not in produtos:
            produtos[produto_id] = produto_model.buscar_por_id(db, produto_id)
        produto = produtos[produto_id]
        if produto is None:
            raise ValidationError("Produto " + str(produto_id) + " não encontrado", sucesso=False)
        if produto["estoque"] < item["quantidade"]:
            raise ValidationError("Estoque insuficiente para " + produto["nome"], sucesso=False)
        total = total + (produto["preco"] * item["quantidade"])

    with db:  # pedido, itens e baixa de estoque: tudo ou nada
        pedido_id = pedido_model.inserir(db, usuario_id, STATUS_PENDENTE, total)
        for item in itens:
            produto = produtos[item["produto_id"]]
            pedido_model.inserir_item(db, pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
            if not produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"]):
                raise ValidationError("Estoque insuficiente para " + produto["nome"], sucesso=False)

    notification_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_todos(db):
    return pedido_model.listar(db)


def listar_por_usuario(db, usuario_id):
    return pedido_model.listar(db, usuario_id)


def atualizar_status(db, pedido_id, dados):
    novo_status = (dados or {}).get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")
    if not pedido_model.existe(db, pedido_id):
        raise NotFoundError("Pedido não encontrado")
    with db:
        pedido_model.atualizar_status(db, pedido_id, novo_status)

    if novo_status == STATUS_APROVADO:
        notification_service.pedido_aprovado(pedido_id)
    elif novo_status == STATUS_CANCELADO:
        notification_service.pedido_cancelado(pedido_id)
