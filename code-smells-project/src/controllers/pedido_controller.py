"""Casos de uso de pedidos."""
import logging

from src.config.settings import STATUS_PEDIDO_VALIDOS, STATUS_PENDENTE, STATUS_PERMITIDOS_AO_DONO
from src.middlewares.errors import ForbiddenError, NotFoundError, ValidationError
from src.models import pedido_model, produto_model, usuario_model
from src.services import notification_service

logger = logging.getLogger(__name__)


class _EstoqueInsuficiente(Exception):
    pass


def _is_int(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _validar_itens(itens):
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if (
            not isinstance(item, dict)
            or not _is_int(item.get("produto_id"))
            or not _is_int(item.get("quantidade"))
            or item["quantidade"] <= 0
        ):
            raise ValidationError("Item inválido: produto_id e quantidade (inteiro positivo) são obrigatórios")


def _resolver_dono(db, dados, solicitante):
    """O dono do pedido é quem chama; só um admin pode criar em nome de outro usuário."""
    usuario_id = dados.get("usuario_id", solicitante["id"])
    if not _is_int(usuario_id) or usuario_id <= 0:
        raise ValidationError("Usuario ID é obrigatório")
    if usuario_id != solicitante["id"]:
        if not usuario_model.is_admin(solicitante):
            raise ForbiddenError("Sem permissão para criar pedido para outro usuário")
        if usuario_model.buscar_por_id(db, usuario_id) is None:
            raise ValidationError("Usuário não encontrado")
    return usuario_id


def criar(db, dados, solicitante):
    if not dados:
        raise ValidationError("Dados inválidos")
    usuario_id = _resolver_dono(db, dados, solicitante)
    itens = dados.get("itens", [])
    _validar_itens(itens)

    total = 0
    precos = {}
    for item in itens:
        produto = produto_model.buscar_por_id(db, item["produto_id"])
        if produto is None:
            raise ValidationError(f"Produto {item['produto_id']} não encontrado", sucesso=False)
        if produto["estoque"] < item["quantidade"]:
            raise ValidationError(f"Estoque insuficiente para {produto['nome']}", sucesso=False)
        precos[produto["id"]] = (produto["preco"], produto["nome"])
        total = total + produto["preco"] * item["quantidade"]

    try:
        with db:  # pedido, itens e estoque: tudo ou nada
            pedido_id = pedido_model.inserir(db, usuario_id, STATUS_PENDENTE, total)
            for item in itens:
                preco, nome = precos[item["produto_id"]]
                pedido_model.inserir_item(db, pedido_id, item["produto_id"], item["quantidade"], preco)
                if not produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"]):
                    raise _EstoqueInsuficiente(nome)
    except _EstoqueInsuficiente as erro:
        raise ValidationError(f"Estoque insuficiente para {erro}", sucesso=False)

    notification_service.notificar_pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_todos(db):
    return pedido_model.listar(db)


def listar_do_usuario(db, usuario_id):
    return pedido_model.listar(db, usuario_id=usuario_id)


def atualizar_status(db, pedido_id, dados, solicitante):
    novo_status = (dados or {}).get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")

    pedido = pedido_model.buscar_por_id(db, pedido_id)
    if pedido is None:
        raise NotFoundError("Pedido não encontrado")

    if not usuario_model.is_admin(solicitante):
        if pedido["usuario_id"] != solicitante["id"]:
            raise ForbiddenError("Sem permissão para alterar este pedido")
        if novo_status not in STATUS_PERMITIDOS_AO_DONO:
            raise ForbiddenError("Somente um administrador pode aplicar este status")

    pedido_model.atualizar_status(db, pedido_id, novo_status)
    notification_service.notificar_mudanca_status(pedido_id, novo_status)
