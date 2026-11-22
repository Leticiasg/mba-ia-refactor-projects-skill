class AppError(Exception):
    status_code = 500

    def __init__(self, message, sucesso=None):
        super().__init__(message)
        self.message = message
        self.sucesso = sucesso

    def to_dict(self):
        corpo = {"erro": self.message}
        if self.sucesso is not None:
            corpo["sucesso"] = self.sucesso
        return corpo


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class NotFoundError(AppError):
    status_code = 404
