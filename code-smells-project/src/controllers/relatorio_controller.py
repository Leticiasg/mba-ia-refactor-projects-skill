"""Relatório de vendas."""
from src.config.settings import FAIXAS_DESCONTO, STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE
from src.models import pedido_model


def _desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


def relatorio_vendas(db):
    resumo = pedido_model.resumo_por_status(db)
    total_pedidos = sum(grupo["quantidade"] for grupo in resumo.values())
    faturamento = sum(grupo["faturamento"] for grupo in resumo.values())
    desconto = _desconto(faturamento)

    def quantidade(status):
        return resumo.get(status, {}).get("quantidade", 0)

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": quantidade(STATUS_PENDENTE),
        "pedidos_aprovados": quantidade(STATUS_APROVADO),
        "pedidos_cancelados": quantidade(STATUS_CANCELADO),
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
