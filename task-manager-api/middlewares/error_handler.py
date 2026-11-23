from flask import jsonify
from werkzeug.exceptions import HTTPException

from middlewares.errors import AppError

ERROR_FIELD = 'error'


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({ERROR_FIELD: error.message}), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        if isinstance(error, HTTPException):  # 404 de rota inexistente, 405 etc.
            return error
        app.logger.exception('Erro não tratado')
        return jsonify({ERROR_FIELD: 'Erro interno do servidor'}), 500
