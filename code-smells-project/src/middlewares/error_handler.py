"""Tratamento de erro centralizado: nunca devolve detalhes internos ao cliente."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.middlewares.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        body = {"erro": error.message}
        if error.sucesso is not None:
            body["sucesso"] = error.sucesso
        return jsonify(body), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        if isinstance(error, HTTPException):
            return error
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
