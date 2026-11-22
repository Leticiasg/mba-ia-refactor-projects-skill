import logging
import sqlite3

from src.config.settings import API_VERSION
from src.middlewares.errors import ValidationError
from src.models import admin_model
from src.models.database import connect_read_only

logger = logging.getLogger(__name__)


def resetar_banco(db):
    with db:
        admin_model.resetar(db)
    logger.warning("Banco de dados resetado por requisição administrativa")


def executar_consulta(caminho_banco, dados):
    sql = (dados or {}).get("sql", "")
    if not isinstance(sql, str) or not sql.strip():
        raise ValidationError("Query não informada")
    if not sql.strip().upper().startswith("SELECT"):
        raise ValidationError("Apenas consultas SELECT são permitidas")

    conexao = connect_read_only(caminho_banco)
    try:
        return admin_model.executar_consulta_leitura(conexao, sql)
    except (sqlite3.Error, sqlite3.Warning):  # Warning: mais de um comando na mesma string
        logger.warning("Consulta administrativa inválida", exc_info=True)
        raise ValidationError("Query inválida")
    finally:
        conexao.close()


def status_sistema(db, ambiente):
    return {
        "status": "ok",
        "database": "connected",
        "counts": admin_model.contar_registros(db),
        "versao": API_VERSION,
        "ambiente": ambiente,
    }


def boas_vindas():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": API_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }
