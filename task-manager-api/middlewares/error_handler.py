import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from middlewares.errors import AppError
from models.database import db

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({"error": error.message}), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):  # 404 de rota, 405, 415 etc. seguem o padrão do Flask
            return error
        db.session.rollback()
        logger.exception("Erro não tratado")
        return jsonify({"error": "Erro interno"}), 500
