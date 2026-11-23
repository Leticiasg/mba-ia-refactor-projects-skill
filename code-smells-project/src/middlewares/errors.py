"""Erros de domínio convertidos em JSON pelo error handler central."""


class AppError(Exception):
    status_code = 500

    def __init__(self, message, extra=None, body=None):
        super().__init__(message)
        self.message = message
        self.extra = extra or {}
        self.body = body


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class NotFoundError(AppError):
    status_code = 404


class ServiceUnavailableError(AppError):
    status_code = 500
