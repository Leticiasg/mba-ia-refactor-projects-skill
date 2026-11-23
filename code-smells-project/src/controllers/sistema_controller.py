import logging
import sqlite3

from src.config.settings import API_VERSAO
from src.middlewares.errors import ServiceUnavailableError
from src.models import admin_model

logger = logging.getLogger(__name__)

ENDPOINTS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


def boas_vindas():
    return {"mensagem": "Bem-vindo à API da Loja", "versao": API_VERSAO, "endpoints": ENDPOINTS}


def health(db, ambiente):
    try:
        counts = admin_model.contagens(db)
    except sqlite3.Error:
        logger.exception("Health check falhou")
        raise ServiceUnavailableError(
            "Banco indisponível", body={"status": "erro", "detalhes": "Banco de dados indisponível"}
        )
    return {"status": "ok", "database": "connected", "counts": counts, "versao": API_VERSAO, "ambiente": ambiente}
