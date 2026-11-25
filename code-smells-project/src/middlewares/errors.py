"""Erros de domínio convertidos em JSON pelo error handler central."""


class AppError(Exception):
    status_code = 500

    def __init__(self, message, sucesso=None):
        super().__init__(message)
        self.message = message
        # Algumas respostas originais trazem "sucesso": false junto do erro.
        self.sucesso = sucesso


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404
