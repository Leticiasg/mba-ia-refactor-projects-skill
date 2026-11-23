import logging
import sqlite3

from src.middlewares.errors import ValidationError
from src.models import admin_model

logger = logging.getLogger(__name__)


def resetar_banco(db):
    admin_model.apagar_tudo(db)
    logger.warning("BANCO DE DADOS RESETADO")


def executar_consulta(database_path, dados):
    sql = dados.get("sql", "")
    if not sql or not isinstance(sql, str):
        raise ValidationError("Query não informada")
    if not sql.strip().upper().startswith("SELECT"):
        raise ValidationError("Apenas consultas SELECT são permitidas")
    try:
        return admin_model.executar_select_somente_leitura(database_path, sql)
    except sqlite3.Error:
        logger.warning("Consulta administrativa inválida", exc_info=True)
        raise ValidationError("Query inválida")
