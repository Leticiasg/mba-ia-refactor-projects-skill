"""Operações administrativas."""
import logging
import sqlite3

from src.middlewares.errors import ValidationError
from src.models import admin_model

logger = logging.getLogger(__name__)


def resetar_banco(db, solicitante):
    admin_model.resetar(db)
    logger.warning("Banco de dados resetado pelo usuário %s", solicitante["id"])


def executar_consulta(readonly_db, dados):
    sql = (dados or {}).get("sql", "")
    if not isinstance(sql, str) or not sql.strip():
        raise ValidationError("Query não informada")
    if not sql.strip().upper().startswith("SELECT"):
        raise ValidationError("Apenas consultas SELECT são permitidas")
    try:
        return admin_model.executar_consulta(readonly_db, sql)
    except (sqlite3.Error, sqlite3.Warning) as erro:  # Warning: mais de uma instrução no texto
        logger.info("Consulta administrativa inválida: %s", erro)
        raise ValidationError("Query inválida")
