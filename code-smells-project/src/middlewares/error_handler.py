import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.middlewares.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        if error.body is not None:
            return jsonify(error.body), error.status_code
        return jsonify({"erro": error.message, **error.extra}), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        if isinstance(error, HTTPException):
            return error
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
