import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from middlewares.errors import AppError
from models.database import db

logger = logging.getLogger(__name__)

ERROR_FIELD = 'error'
INTERNAL_ERROR_MESSAGE = 'Erro interno'


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        db.session.rollback()
        return jsonify({ERROR_FIELD: error.message}), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return error
        db.session.rollback()
        logger.exception('Erro não tratado')
        return jsonify({ERROR_FIELD: INTERNAL_ERROR_MESSAGE}), 500
