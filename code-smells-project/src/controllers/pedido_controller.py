import logging

from src.config.settings import STATUS_PEDIDO_VALIDOS, STATUS_PENDENTE
from src.middlewares.errors import ValidationError
from src.models import pedido_model, produto_model
from src.services import notification_service

logger = logging.getLogger(__name__)


def _erro_pedido(mensagem):
    return ValidationError(mensagem, extra={"sucesso": False})


def _normalizar_itens(itens):
    normalizados = []
    for item in itens:
        try:
            produto_id = int(item["produto_id"])
            quantidade = int(item["quantidade"])
        except (TypeError, KeyError, ValueError):
            raise ValidationError("Item de pedido inválido")
        if quantidade <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")
        normalizados.append((produto_id, quantidade))
    return normalizados


def criar(db, dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens or not isinstance(itens, list):
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    itens = _normalizar_itens(itens)
    produtos = produto_model.buscar_por_ids(db, [produto_id for produto_id, _ in itens])

    total = 0
    for produto_id, quantidade in itens:
        produto = produtos.get(produto_id)
        if produto is None:
            raise _erro_pedido(f"Produto {produto_id} não encontrado")
        if produto["estoque"] < quantidade:
            raise _erro_pedido("Estoque insuficiente para " + produto["nome"])
        total = total + produto["preco"] * quantidade

    with db:  # pedido, itens e estoque: tudo ou nada
        pedido_id = pedido_model.inserir(db, usuario_id, STATUS_PENDENTE, total)
        for produto_id, quantidade in itens:
            produto = produtos[produto_id]
            pedido_model.inserir_item(db, pedido_id, produto_id, quantidade, produto["preco"])
            if not produto_model.baixar_estoque(db, produto_id, quantidade):
                raise _erro_pedido("Estoque insuficiente para " + produto["nome"])

    notification_service.notificar_pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar(db):
    return pedido_model.listar(db)


def listar_por_usuario(db, usuario_id):
    return pedido_model.listar(db, usuario_id=usuario_id)


def atualizar_status(db, pedido_id, dados):
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")
    with db:
        pedido_model.atualizar_status(db, pedido_id, novo_status)
    notification_service.notificar_status_pedido(pedido_id, novo_status)
