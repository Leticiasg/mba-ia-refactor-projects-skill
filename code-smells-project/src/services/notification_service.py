"""Notificações de pedido. Hoje só registram em log; é o ponto de integração com e-mail/SMS/push."""
import logging

from src.config.settings import STATUS_APROVADO, STATUS_CANCELADO

logger = logging.getLogger(__name__)


def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info("Notificação (e-mail, SMS, push): pedido %s criado para o usuário %s", pedido_id, usuario_id)


def notificar_mudanca_status(pedido_id, status):
    if status == STATUS_APROVADO:
        logger.info("Notificação: pedido %s aprovado, preparar envio", pedido_id)
    elif status == STATUS_CANCELADO:
        logger.info("Notificação: pedido %s cancelado", pedido_id)
